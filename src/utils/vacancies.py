import json
import time
from datetime import datetime
from typing import Any

import psycopg2
import requests
from src.conf.constants import ID_RUSSIA_HH, NOT_DATA
from loguru import logger
from tqdm import trange
import re


class Mixin:
    """
    Класс примеси содержит статические методы, позволяющие выполнять различные задачи наследникам.
    """

    def one_level(self, dict_vak: dict, key_1: str) -> str:
        """
        Проверка и обработка данных из исходного словаря.
        Один уровень вложенности ключей в словаре.
        :param dict_vak: Словарь вакансии (анализируемый), dict.
        :param key_1: Ключ 1-го уровня вложенности анализируемого словаря, str.
        :return: Строковые данные, str.
        """
        try:
            if all(dict_vak.get(key_1)):
                return self.del_space(self.del_html_tag(dict_vak[key_1]))
        except (TypeError, AttributeError):
            return NOT_DATA

    def two_levels(self, dict_vak: dict, key_1: str, key_2: str) -> str:
        """
        Проверка и обработка данных из исходного словаря.
        Два уровня вложенности ключей в словаре.
        :param dict_vak: Словарь вакансии (анализируемый), dict.
        :param key_1: Ключ 1-го уровня вложенности анализируемого словаря, str.
        :param key_2: Ключ 2-го уровня вложенности анализируемого словаря, str.
        :return: Строковые данные, str.
        """
        try:
            if all(dict_vak.get(key_1).get(key_2)):
                return self.del_space(self.del_html_tag(dict_vak[key_1][key_2]))
        except (TypeError, AttributeError):
            return NOT_DATA

    @staticmethod
    def one_level_salary(dict_vak: dict, key_1: str) -> int:
        """
        Проверка и обработка данных по зарплате из исходного словаря.
        Один уровень вложенности ключей в словаре.
        :param dict_vak: Словарь вакансии (анализируемый), dict.
        :param key_1: Ключ 1-го уровня вложенности анализируемого словаря, str.
        :return: Выводит данные о зарплате, int.
        """
        salary = 0
        try:
            if dict_vak.get(key_1) != 0:
                salary = dict_vak[key_1]
        except (TypeError, AttributeError):
            pass
        return salary

    @staticmethod
    def two_levels_salary(dict_vak: dict, key_1: str, key_2: str) -> int:
        """
        Проверка и обработка данных по зарплате из исходного словаря.
        Два уровня вложенности ключей в словаре.
        :param dict_vak: Словарь вакансии (анализируемый), dict.
        :param key_1: Ключ 1-го уровня вложенности анализируемого словаря, str.
        :param key_2: Ключ 2-го уровня вложенности анализируемого словаря, str.
        :return: Выводит данные о зарплате, 0.
        """
        salary = 0
        try:
            if all(str(dict_vak.get(key_1).get(key_2))):
                if str(dict_vak.get(key_1).get(key_2)) != 'None':
                    salary = dict_vak[key_1][key_2]
        except (TypeError, AttributeError):
            pass
        return salary

    @staticmethod
    def del_space(txt: str) -> str:
        """
        Удаляет лишние пробелы в тексте.
        :param txt: Строка для анализа, str.
        :return: Строка с одинарными пробелами, str.
        """
        # Удаляем лишние пробелы в тексте (в начале, в конце, двойные, тройные),
        # оставляя по одному между словами.
        txt = ' '.join(txt.strip().split())
        # txt = re.sub(r'\s+', ' ', txt.strip())
        return txt

    @staticmethod
    def del_html_tag(txt: str) -> str:
        """
        Удаляет все html-теги из текста.
        :param txt: Строка для анализа, str.
        :return: Строка без html-тегов, str.
        """
        txt = re.sub(r'\<[^>]*\>', '', txt)
        return txt

    @staticmethod
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

    @staticmethod
    def foreign_key(ref_list: list[dict], string: str, id_col: str, val_col: str) -> int:
        """
        Возвращает вторичный ключ связанной таблицы.
        :param ref_list: Список словарей связанной таблицы, list[dict].
        :param string: Проверяемое значение, str.
        :param id_col: Наименования поля id, str.
        :param val_col: Наименование сравниваемого поля, str.
        :return: id вторичного ключа, int.
        """
        try:
            for dict_value in ref_list:
                if dict_value[val_col] == string:
                    return int(dict_value[id_col])
        except (TypeError, AttributeError):
            return -1


class VacHH(Mixin):
    """
    Получение данных по API с hh.ru, их обработка и сохранение.
    """

    def __init__(self, db_name: str, params: dict, area: int = ID_RUSSIA_HH, only_with_salary: bool = True,
                 salary: int = 1, per_page: int = 100) -> None:
        self.__url = 'https://api.hh.ru/vacancies'
        self.__area = area  # Поиск по-умолчанию осуществляется по вакансиям России (id=113)
        self.__only_with_salary = only_with_salary
        self.__salary = salary
        self.__per_page = per_page
        self.size_dict = 0  # Счётчик количества словарей с вакансиями
        self.__db_name = db_name
        self.__params = params

    def request_to_api(self, page: int = 0) -> str:
        """
        Получение запроса по api
        :page: Индекс страницы поиска HH.
        :return: ответ запроса, <class 'requests.models.Response'>.
        """
        try:
            parameters = {
                'area': self.__area,
                'page': page,
                'per_page': self.__per_page,
                'salary': self.__salary,
                'only_with_salary': self.__only_with_salary
            }

            # Отправляем запрос к API
            data_prof = requests.get(url=self.__url, params=parameters).text
            logger.info(f'{self.size_dict + 1 if self.size_dict == 0 else self.size_dict // 100 + 1}. '
                        f'Запрос к АPI hh.ru ({self.__url}) выполнен успешно')
            return data_prof
        except Exception as e:
            logger.error(f'Ошибка при получении данных с {self.__url} ({self.__class__.__name__}). {e}')

    def vacancies_all(self) -> None:
        """
        Считывает первые 2000 вакансий и сохраняет их в базу данных.
        """
        employers: list[tuple] = []  # работодатели
        currency: list[tuple] = []  # валюта
        schedule: list[tuple] = []  # график работы
        employment: list[tuple] = []  # занятость
        experience: list[tuple] = []  # опыт работы
        vak_db = []  # список вакансий
        try:
            for page in trange(20, desc='Подождите, пожалуйста. Собираем данные', initial=1):
                # Преобразуем текст ответа запроса в словарь Python.
                js_obj = json.loads(self.request_to_api(page))

                # Получем количество записей
                self.size_dict += len(js_obj['items'])

                for value in js_obj['items']:
                    row_db = [
                        value["published_at"].split('T')[0],  # дата публикации
                        self.one_level(value, "name"),  # должность
                        self.two_levels(value, "employer", "name"),  # работодатель
                        self.two_levels_salary(value, "salary", "from"),  # зарплата от
                        self.two_levels_salary(value, "salary", "to"),  # зарплата до
                        self.two_levels(value, "salary", "currency"),  # валюта
                        self.two_levels(value, "schedule", "name"),  # график работы
                        self.two_levels(value, "employment", "name"),  # занятость
                        self.two_levels(value, "experience", "name"),  # опыт работы
                        # требования к соискателю
                        self.two_levels(value, "snippet", "requirement"),
                        # обязанности
                        self.two_levels(value, "snippet", "responsibility"),
                        self.two_levels(value, "address", 'raw'),  # адрес
                        self.one_level(value, "alternate_url"),  # URL
                    ]
                    vak_db.append(row_db)

                    # Работодатели, валюта, график, занятость, опыт.
                    employers.append((int(value["area"]["id"]),
                                      self.two_levels(value, "employer", "name")))
                    currency.append((self.two_levels(value, "salary", "currency"),))
                    schedule.append((self.two_levels(value, "schedule", "name"),))
                    employment.append((self.two_levels(value, "employment", "name"),))
                    experience.append((self.two_levels(value, "experience", "name"),))

                # Проверка на последнюю страницу, если вакансий меньше 2000
                if (js_obj['pages'] - page) <= 1:
                    break

                # Задержка, чтобы не нагружать сервисы hh.
                time.sleep(0.03)

            # Заполнение справочных таблиц
            reference_tables = [currency, schedule, employment, experience]
            names_tables = ['currency', 'schedule', 'employment', 'experience']
            i: int
            for i in range(len(names_tables)):
                reference_tables[i] = sorted(tuple(set(reference_tables[i])))
                self.insert_table(names_tables[i], names_tables[i] + '_name', reference_tables[i])

            # Заполнение таблицы employers
            employers = sorted(tuple(set(employers)))
            self.insert_table('employers', 'area_id, employer_name', employers)

            # Заполнение таблицы vacancies
            self.db_insert_table_vacancies(vak_db)

            logger.info(f'Получено {self.coord_words_num(self.size_dict)}. Всего работодателей: {len(employers)}')
        except KeyError as e:
            logger.error(f'Ошибка обращения к полученным данным ({self.__class__.__name__}). {e}')

    def db_insert_table_vacancies(self, vak_db: list[list]) -> None:
        """
        Заполнение данными таблицы vacancies ("Вакансии").
        :param vak_db: Список списков вакансий, list[list].
        """
        # Получение списков словарей таблиц связанных по вторичному ключу c табл. vacancies.
        dict_employers = self.select_data_table('employers', ['employer_id', 'area_id', 'employer_name'])
        dict_currency = self.select_data_table('currency', ['currency_id', 'currency_name'])
        dict_schedule = self.select_data_table('schedule', ['schedule_id', 'schedule_name'])
        dict_employment = self.select_data_table('employment', ['employment_id', 'employment_name'])
        dict_experience = self.select_data_table('experience', ['experience_id', 'experience_name'])

        try:
            # Формирование списка кортежей для заполнения таблицы vacancies
            vacancies_db = []
            for data_list in vak_db:
                vacancy = (
                    datetime.strptime(data_list[0], '%Y-%m-%d'),
                    data_list[1],
                    self.foreign_key(dict_employers, data_list[2], 'employer_id', 'employer_name'),
                    data_list[3],
                    data_list[4],
                    self.foreign_key(dict_currency, data_list[5], 'currency_id', 'currency_name'),
                    self.foreign_key(dict_schedule, data_list[6], 'schedule_id', 'schedule_name'),
                    self.foreign_key(dict_employment, data_list[7], 'employment_id', 'employment_name'),
                    self.foreign_key(dict_experience, data_list[8], 'experience_id', 'experience_name'),
                    data_list[9],
                    data_list[10],
                    data_list[11],
                    data_list[12]
                )
                if vacancy.count(-1) == 0:
                    vacancies_db.append(vacancy)
                else:
                    continue
            # Заполнение таблицы БД vacancies (вакансии)
            self.insert_table('vacancies', 'date_publication, '
                                           'position_employee,'
                                           'employer_id, '
                                           'salary_from, '
                                           'salary_to, '
                                           'currency_id, '
                                           'schedule_id, '
                                           'employment_id, '
                                           'experience_id, '
                                           'applicant_requirements, '
                                           'duties, '
                                           'employer_address, '
                                           'url', vacancies_db)
        except Exception as err:
            logger.error(f'Ошибка создания списка вакансий ({self.__class__.__name__}): {err}')

    def insert_table(self, table: str, columns: str, list_table: list[tuple]) -> None:
        """
        Заполнение таблицы БД данными.
        :param table: Имя заполняемой таблицы, str.
        :param columns: Имена полей, str.
        :param list_table: Список картежей с данными для заполнения таблицы, list[tuple].
        """
        conn = psycopg2.connect(dbname=self.__db_name, **self.__params)
        try:
            with conn:
                with conn.cursor() as cur:
                    database_request = (f"INSERT INTO  {table}({columns})"
                                        f"VALUES ({', '.join(['%s'] * len(list_table[0]))})")
                    cur.executemany(database_request, list_table)
            logger.info(f'Таблица {table} БД {self.__db_name} заполнена данными успешно')
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error(f'Заполнение таблицы БД данными ({self.__class__.__name__}): {error}')
            exit(1)
        finally:
            conn.close()

    def select_data_table(self, table: str, columns_list: list) -> list[dict[Any, Any]]:
        """
        Получение данных из таблицы БД с сортировкой по возрастанию значения ключевого поля.
        :param table: Имя таблицы, из которой извлекаются все данные, str.
        :param columns_list: Список заголовков таблицы, list.
        :return: Список словарей, содержащий данные таблицы, list[dict[Any, Any]].
        """
        conn = psycopg2.connect(dbname=self.__db_name, **self.__params)
        try:
            with conn:
                with conn.cursor() as cur:
                    # Формируем запрос
                    database_request = (f"SELECT * FROM {table} "
                                        f"ORDER BY {columns_list[0]}")
                    cur.execute(database_request)
                    # Формируем список словарей
                    fetch = cur.fetchall()
                    result = []
                    for row in fetch:
                        result.append(dict(zip(columns_list, row)))
            logger.info(f'Данные из {table} получены успешно')
            return result
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error(f'Получение данных из таблицы БД с сортировкой по возрастанию ({self.__class__.__name__}): {error}')
            exit(1)
        finally:
            conn.close()

    def __str__(self) -> str:
        return f'Получение и вставка в БД сведений о вакансиях с сервиса hh.ru по API {self.__url}'

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(url: {self.__url}, area: {self.__area},"
                f" only_with_salary: {self.__only_with_salary}, salary: {self.__salary},"
                f" per_page: {self.__per_page}, size_dict: {self.size_dict}),"
                f" БД {self.__db_name}, host: {self.__params[0]}, port: {self.__params[3]}")
