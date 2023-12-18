import json
from typing import Any

import psycopg2
import requests
from src.conf.constants import URL_AREAS_HH, ID_RUSSIA_HH, DB_NAME
from loguru import logger


class AreasHH:
    """
    Класс получения справочника по API
    для поиска регионов/населённых пунктов России и размещения данных в БД.
    """

    def __init__(self, url: str, area: str, db_name: str, params: dict) -> None:
        self.__url = url  # Поиск регионов в России
        self.__id = ID_RUSSIA_HH  # По-умолчанию Россия
        self.__area = area.lower()
        self.__db_name = db_name
        self.__params = params

    def request_to_api(self) -> None:
        """
        Получение запроса о регионах в России по api.
        Заполнение справочных таблиц о регионах.
        """
        try:
            # Посылаем запрос к API, преобразуем его в словарь, получая список.
            data_areas = json.loads(requests.get(url=self.__url).text)['areas']
            logger.info(f'Данные о регионах/населённых пунктах с {self.__url} получены успешно')
            # Преобразование данных и заполнение таблиц
            self.db_insert_tables_regions(data_areas)  # регионы
            self.db_insert_tables_cities(data_areas)  # населённые пункты
        except Exception as e:
            logger.error(f'Ошибка при получении данных с {self.__url}. {e}')

    def db_insert_tables_regions(self, data_areas: list) -> None:
        """
        Заполнение таблицы с данными о регионах.
        :param data_areas: Список данных с регионами/населёнными пунктами.
        """
        # формируем список кортежей данных о регионах и городах федерального значения
        regions = []
        for dict_region in data_areas:
            if int(dict_region['parent_id']) == self.__id:
                regions.append((int(dict_region['id']), dict_region['name'],))

        # заполняем таблицу БД regions
        self.insert_table('regions', 'region_id, region_name', regions)

    def db_insert_tables_cities(self, data_areas: list) -> None:
        """
        Заполнение таблицы с данными о населённых пунктах.
        :param data_areas: Список данных с регионами/населёнными пунктами.
        """
        # формируем список кортежей данных о населённых пунктах
        cities = []
        for dict_region in data_areas:
            if int(dict_region['parent_id']) == self.__id:
                id_region = int(dict_region['id'])
                if len(dict_region['areas']) != 0:
                    for dict_city in dict_region['areas']:
                        cities.append((int(dict_city['id']), id_region, dict_city['name'],))

        # Заполняем таблицу БД cities
        self.insert_table('cities', 'city_id, region_id, city_name', cities)

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
            logger.error(error)
            exit(1)
        finally:
            conn.close()

    def __str__(self) -> str:
        return f'Заполнение справочника (таблицы БД) регионов/городов России с сервиса hh.ru по API {self.__url}'

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(url: {self.__url}, id: {self.__id}, "
                f"регион: {self.__area.upper()}, БД: {self.__db_name}, "
                f"host: {self.__params[0]}, port: {self.__params[3]})")
