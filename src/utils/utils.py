import psycopg2
from loguru import logger

from src.conf.constants import PATH_LOGS, URL_AREAS_HH, DB_NAME, SCRIPT_DBCREATE, SCRIPT_DBCREATETABLES, \
    SCRIPT_DBINSERTTABLES, UPDATE_DAYS, LOG_FULL, LOG_AUTO, LOG_USER, LOG_NOUPDATE
from datetime import datetime

from src.utils.areas import AreasHH
from src.utils.creationdb import CreationDB


def log_json():
    """
    Запись логов в файл.
    """
    logger.remove(0)
    logger.add(PATH_LOGS,
               format="{time:YYYY-MM-DD HH:mm:ss} :: {level} :: {message}",
               rotation='10 KB', compression='zip')


def create_database(params: dict) -> None:
    """
    Создание БД, таблиц, заполнение справочных таблиц.
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
            db.insert_tables(SCRIPT_DBINSERTTABLES)

            # Заполнение таблиц
            areas_update(params)  # Регионы/населённые пункты
            logger.debug(LOG_FULL)  # Лог: полное обновление прошло успешно
        conn.commit()
        conn.close()

    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(error)
        exit(1)


def read_logfile() -> tuple[int, str, bool]:
    """
    Чтение .log-файла, поиск последней записи,
    содержащей информацию об обновлении БД.
    :return: Кортеж, содержащий количество прошедших дней и флаг, tuple[int, str, bool].
    """
    with open(PATH_LOGS, 'r', encoding='utf8') as file:
        lines = [line for line in file]

    # Ищем нужную строку
    for str_log in reversed(lines):
        try:
            log_date = datetime.strptime(str_log.split(' :: ')[0], '%Y-%m-%d %H:%M:%S')
            now = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
            num_days = (now - log_date).days  # прошло дней
            log_text = str_log.split(' :: ')[-1].strip()  # текст лога

            if log_text == LOG_FULL or log_text == LOG_AUTO or log_text == LOG_USER or log_text == LOG_NOUPDATE:
                if num_days >= UPDATE_DAYS:
                    return num_days, f'{log_date:%d}.{log_date:%m}.{log_date:%Y}', True
                else:
                    return num_days, f'{log_date:%d}.{log_date:%m}.{log_date:%Y}', False
            else:
                return num_days, f'{now:%d}.{now:%m}.{now:%Y}', False
        except Exception as err:
            logger.error(err)
            continue


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
        logger.error(error)
        exit(1)


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
        logger.error(error)
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
    truncate_tables_full(DB_NAME, params, 'regions, cities, employers, '
                                          'currency, schedule, employment, '
                                          'experience, vacancies')
    # Заполнение справочных таблиц
    db = CreationDB(params, DB_NAME)
    db.insert_tables(SCRIPT_DBINSERTTABLES)

    # Обновление данных в БД
    areas_update(params)
