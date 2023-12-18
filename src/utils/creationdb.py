import psycopg2

from src.conf.constants import DB_NAME
from loguru import logger


class CreationDB:

    def __init__(self, params: dict, db_name: str = DB_NAME) -> None:
        self.__db_name = db_name
        self.__params = params

    def create_database(self, path_dbcreate: str) -> None:
        """
        Создание базы данных из скрипта .sql
        """
        try:
            conn = psycopg2.connect(dbname='postgres', **self.__params)
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute(f'CREATE DATABASE {self.__db_name}')
            # Настраиваем БД из файла настроек
            try:
                with conn:
                    with cur as cursor:
                        cursor.execute(self.sql_read(path_dbcreate))
                logger.info(f"БД {self.__db_name} успешно создана")
            finally:
                conn.close()
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error(error)
            exit(1)

    def create_tables(self, path_dbcreatetables: str) -> None:
        """
        Создание таблиц БД из скрипта .sql
        """
        self.sql_script(path_dbcreatetables)
        logger.info(f"Таблицы БД {self.__db_name} успешно созданы")

    def insert_tables(self, path_dbinserttables: str) -> None:
        """
        Заполнение таблиц БД из скрипта .sql
        """
        self.sql_script(path_dbinserttables)
        logger.info(f"Справочные таблицы БД {self.__db_name} успешно заполнены")

    def sql_script(self, path: str) -> None:
        """
        Считывание и запуск sql скрипта из файла .sql
        """
        try:
            conn = psycopg2.connect(dbname=self.__db_name, **self.__params)
            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(self.sql_read(path))
            finally:
                conn.close()
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error(error)
            exit(1)

    @staticmethod
    def sql_read(path: str) -> str:
        """
        Чтение .sql файла.
        :param path: Путь к файлу, str.
        :return: sql-скрипт, str.
        """
        try:
            with open(path, 'r', encoding='utf-8') as sql:
                return sql.read()
        except FileNotFoundError:
            raise FileNotFoundError(f'Отсутствует файл {path}.')

    def __str__(self) -> str:
        return f'Создание БД {self.__db_name}, таблиц, заполнение справочных таблиц данными '

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}({self.__db_name}, "
                f"host: {self.__params['host']}, port: {self.__params['port']})")
