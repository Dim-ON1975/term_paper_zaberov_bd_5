import psycopg2
from loguru import logger

from src.conf.config import config
from src.conf.constants import PATH_LOGS, URL_AREAS_HH, DB_NAME, SCRIPT_DBCREATE, SCRIPT_DBCREATETABLES, \
    LOG_FULL, LOG_USER, LOG_NOUPDATE, ID_RUSSIA_HH
from src.utils.dbmanager import DBManager

from src.utils.areas import AreasHH
from src.utils.creationdb import CreationDB
from src.utils.vacancies import VacHH


def log_json():
    """
    Запись логов в файл.
    """
    logger.remove(0)
    logger.add(open(PATH_LOGS, 'w', encoding='utf8'), format="{time:YYYY-MM-DD HH:mm:ss} :: {level} :: {message}")


def create_database(params: dict) -> None:
    """
    Создание БД, таблиц, заполнение таблиц.
    :param params: Параметры подключения к БД, dict.
    """
    try:
        db = CreationDB(params, DB_NAME)  # экз. класса для создания БД

        conn = psycopg2.connect(dbname='postgres', **params)
        conn.autocommit = True
        cur = conn.cursor()

        # Если БД с указанным именем не существует, то создаём её
        cur.execute(f"SELECT 1 FROM pg_database "
                    f"WHERE datname = '{DB_NAME}'")
        if cur.fetchone() is None:
            print('Подождите, пожалуйста, обновляем данные...')
            # Создание БД, таблиц, заполнение некоторых таблиц справочными данными
            db.create_database(SCRIPT_DBCREATE)
            db.create_tables(SCRIPT_DBCREATETABLES)

            # Заполнение таблиц
            areas_update(params)  # Регионы/населённые пункты
            vacancies_update(params)  # Работодатели, вакансии
            logger.info(LOG_FULL)  # Лог: полное обновление прошло успешно
            save_history()  # запись истории в БД
        conn.commit()
        conn.close()

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'Создание БД, таблиц, заполнение таблиц: {error}')
        exit(1)


def save_history() -> None:
    """
    Чтение .log-файла, поиск последней записи, содержащей информацию
    об обновлении БД и запись данных в таблицу history.
    """
    with open(PATH_LOGS, 'r', encoding='utf8') as file:
        lines = [line for line in file]

    # Ищем нужную строку
    data_log = []
    for str_log in reversed(lines):
        try:
            text = str_log.split(' :: ')
            log_text = text[-1].strip()  # текст лога, str
            log_timestamp = text[0].strip()  # дата и время, str

            if log_text == LOG_FULL or log_text == LOG_USER or log_text == LOG_NOUPDATE:
                if len(data_log) == 0:
                    data_log.append(log_timestamp)
            if 'Поиск по запросу : ' in str_log or 'Поиск по-умолчанию : ' in str_log:
                if len(data_log) == 1:
                    data_log.append(str_log.split(' : ')[1].strip())
                data = tuple(data_log)
                insert_history(data)
                break
        except Exception as error:
            logger.error(f'Чтение лога и запись данных в таблицу history: {error}')
            continue


def insert_history(data: tuple) -> None:
    """
    Сохранение записи о запросе пользователя в таблицу БД.
    :param data: Кортеж с данными, tuple.
    """
    params = config()  # параметры подключения к БД
    conn = psycopg2.connect(dbname=DB_NAME, **params)
    try:
        with conn:
            with conn.cursor() as cur:
                if len(data) > 2:
                    data = data[len(data) - 2:]
                database_request = (f"INSERT INTO  history(history_datetime, history_area)"
                                    f"VALUES ({', '.join(['%s'] * len(data))})")
                cur.execute(database_request, data)
        logger.info('История запроса сохранена в БД')
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'Заполнение таблицы history: {error}')
        exit(1)
    finally:
        conn.close()


def select_history() -> tuple:
    """
    Извлечение данных о последнем событии из таблицы history.
    :return: Кортеж с последними данными из таблицы history, tuple.
    """
    params = config()  # параметры подключения к БД
    conn = psycopg2.connect(dbname=DB_NAME, **params)
    try:
        with conn:
            with conn.cursor() as cur:
                database_request = ('SELECT * FROM history '
                                    'ORDER BY history_datetime DESC '
                                    'LIMIT 1')
                cur.execute(database_request)
                # Распаковка полученных данных
                data = cur.fetchall()
                history_cur = []
                for i in data:
                    for j in range(len(i)):
                        history_cur.append(i[j])
                return tuple(history_cur)
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'Запрос к таблице history: {error}')
        exit(1)
    finally:
        conn.close()


def areas_update(params: dict) -> None:
    """
    Заполнение справочных данных БД по регионам/населённым пунктам.
    :param params: Параметры запроса к БД, dict
    """
    # Получение данных по регионам/населённым пунктам и заполнение справочных таблиц
    try:
        areas = AreasHH(URL_AREAS_HH, 'Россия', DB_NAME, params)
        areas.request_to_api()
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'Заполнение таблицы areas: {error}')
        exit(1)


def vacancies_update(params: dict) -> None:
    """
    Заполнение данных о работодателях и вакансиях.
    :param params:  Параметры запроса к БД, dict.
    """
    area = input('Введите название региона/города: ').strip().lower()
    # Поиск id
    id_area = area_id(area, params)

    # Поиск данных, заполнение таблиц
    try:
        vac = VacHH(db_name=DB_NAME, params=params, area=id_area)
        vac.vacancies_all()
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'Заполнение таблицы vacancies: {error}')
        exit(1)


def area_id(area: str, params: dict) -> int:
    """
    Поиск id региона/города.
    :param area: Регион/город, указанный пользователем.
    :param params:  Параметры запроса к БД, dict.
    :return: ID для поиска данных по конкретному региону.
    """
    # Поиск id региона/города в БД
    conn = psycopg2.connect(dbname=DB_NAME, **params)
    try:
        with conn:
            with conn.cursor() as cur:
                sql_query = f"SELECT area_id FROM areas WHERE area_name ~~* '{area}%'"
                cur.execute(sql_query)
                for i in cur.fetchall():
                    id_area = i[0]
        try:
            logger.info(f'Поиск по запросу : {area} : id = {id_area})')
            return id_area
        except:
            print('Введены некорректные данные. Ищем для Вас вакансии на территории России.')
            id_area = ID_RUSSIA_HH
            logger.info(f'Поиск по-умолчанию : Россия : id = {id_area})')
            return id_area
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'Поиск id региона/города (таблица areas): {error}')
        exit(1)
    finally:
        conn.close()


def truncate_tables_full(db_name: str, params: dict, tables: str) -> None:
    """
    Удаление данных из всех таблиц.
    :param db_name: Имя БД, str.
    :param params: Параметры подключения к БД, dict.
    :param tables: Перечень очищаемых таблиц, str.
    """
    conn = psycopg2.connect(dbname=db_name, **params)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(f'TRUNCATE {tables} RESTART IDENTITY')
        logger.info(f'Таблицы {tables} БД {db_name} очищены')
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'Удаление данных из всех таблиц: {error}')
        exit(1)
    finally:
        conn.close()


def update_desired(params: dict) -> None:
    """
    Обновление БД по запросу пользователя.
    :param params: Параметры подключения к БД, dict.
    """
    print('Подождите, пожалуйста, обновляем данные...')
    # Удаление данных из всех таблиц.
    truncate_tables_full(DB_NAME, params, 'areas, employers, '
                                          'currency, schedule, employment, '
                                          'experience, vacancies')

    # Обновление данных в БД
    areas_update(params)
    vacancies_update(params)
    logger.info(LOG_USER)  # Лог: полное обновление прошло успешно
    save_history()  # запись истории в БД


def coord_words_num(digit) -> str:
    """
    Согласование слова "вакансии" с числительными.
    :param digit: Числительное для согласования, int.
    :return: Слово "вакансии", согласованное с числительным, str.
    """
    if digit % 10 == 1 and digit != 11:
        return f'{digit} вакансия'
    elif digit % 10 in [2, 3, 4] and digit not in [12, 13, 14]:
        return f'{digit} вакансии'
    else:
        return f'{digit} вакансий'


def print_companies_and_vacancies_count() -> None:
    """
    Выводит на экран ТОП-10 компаний, сгруппированных по количеству вакансий.
    """
    params = config()
    db = DBManager(DB_NAME, params)
    lst_top10 = db.get_companies_and_vacancies_count()
    print('---------------------------------------\n'
          'ТОП-10 компаний по количеству вакансий:\n'
          '---------------------------------------')
    for company in lst_top10:
        print(f'{company["count"]:<3} - {company["employer_name"]:<15}')


def print_all_vacancies() -> None:
    """
    Вывод информации и вакансий на экран вакансий.
    """
    params = config()
    db = DBManager(DB_NAME, params)
    vacancies = db.get_all_vacancies()
    on_screen(vacancies)


def print_vacancies_with_higher_salary() -> None:
    """
    Вывод на экран списка всех вакансий, у которых зарплата выше средней по всем вакансиям.
    """
    params = config()
    db = DBManager(DB_NAME, params)
    vacancies = db.get_vacancies_with_higher_salary()
    on_screen(vacancies)


def print_vacancies_with_keyword() -> None:
    """
    Вывод на экран вакансий, найденных по ключевому слову.
    """
    word = input('Введите ключевое слово: ')
    params = config()
    db = DBManager(DB_NAME, params)
    vacancies = db.get_vacancies_with_keyword(word)
    if len(vacancies) != 0:
        on_screen(vacancies)
    else:
        print('Мы не нашли вакансии по Вашему запросу')


def on_screen(vacancies: list[dict]) -> None:
    """
    Вывод вакансий на экран.
    :param vacancies: Список словарей с вакансиями, list[dict].
    """
    try:
        number_of_vacancies = int(input(f'\nПо запросу найдено всего {coord_words_num(len(vacancies))}.\n'
                                        f'Какое количество вакансий Вы хотите увидеть? '))
        vacancies = vacancies[:int(number_of_vacancies)]
        print_vacancies(vacancies)
        logger.info(f'Выведено на экран {coord_words_num(len(vacancies))}')
    except (Exception, psycopg2.DatabaseError) as error:
        if len(vacancies) < 10:
            print_vacancies(vacancies)
        else:
            print_vacancies(vacancies[:10])
        logger.error(f'Выбор количества вакансий для отображения: {error}')
        logger.info(f'Выведено на экран {coord_words_num(len(vacancies))}')


def print_vacancies(vacancies: list[dict]) -> None:
    """
    Вывод вакансий на экран.
    :param vacancies: Список словарей с вакансиями, list[dict].
    """
    translator = {'date_publication': 'Дата: ',
                  'position_employee': 'Должность: ',
                  'employer_name': 'Работодатель: ',
                  'salary_from': 'Зарплата от: ',
                  'salary_to': 'Зарплата до: ',
                  'currency_name': 'Валюта: ',
                  'schedule_name': 'График: ',
                  'employment_name': 'Занятость: ',
                  'experience_name': 'Опыт: ',
                  'applicant_requirements': 'Требования: ',
                  'duties': 'Обязанности: ',
                  'employer_address': 'Адрес: ',
                  'url': 'URL: '}

    print('=' * 14)
    for vacancy in vacancies:
        for key, value in translator.items():
            print(f'{value:<14}{vacancy[key]}')
        print('=' * 14)


def message_avg_salary() -> str:
    """
    Вывод информации о средней зарплате по всем вакансиям.
    :return: Сообщение о средней зарплате, str.
    """
    try:
        params = config()
        db = DBManager(DB_NAME, params)
        vacancies = db.get_all_vacancies()
        avg_salary_from = round(db.get_avg_salary()[0]['avg_salary'], 2)
        avg_salary_to = round(db.get_avg_salary()[1]['avg_salary'], 2)
        avg_salary = round((avg_salary_from + avg_salary_to) / 2, 2)
        message = (f'\nВсего найдено {coord_words_num(len(vacancies))} '
                   f'cо средней зарплатой {avg_salary} '
                   f'(от {avg_salary_from} до {avg_salary_to}) руб.\n')
        return message
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f'Вывод средней: {error}')
        print('Что-то пошло не так...')
        exit(1)
