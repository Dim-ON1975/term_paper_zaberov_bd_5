import psycopg2

from src.conf.constants import DB_NAME


class CreationDB:

    def __init__(self, params: dict, db_name: str = DB_NAME) -> None:
        self.__db_name = db_name
        self.__params = params

    def create_database(self, path_dbcreate: str) -> str:
        """
        Создание базы данных из скрипта .sql
        """
        try:
            conn = psycopg2.connect(dbname='postgres', **self.__params)
            conn.autocommit = True
            cur = conn.cursor()
            cur.execute(f'DROP DATABASE IF EXISTS {self.__db_name} WITH (FORCE)')
            cur.execute(f'CREATE DATABASE {self.__db_name}')
            with conn:
                with cur as cursor:
                    cursor.execute(self.sql_read(path_dbcreate))
            return f"БД {self.__db_name} успешно создана"
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            exit(1)

    def create_tables(self, path_dbcreatetables: str) -> str:
        """
        Создание таблиц БД из скрипта .sql
        """
        self.sql_script(path_dbcreatetables)
        return f"Таблицы БД {self.__db_name} успешно созданы"

    def insert_tables(self, path_dbinserttables: str) -> str:
        """
        Заполнение таблиц БД из скрипта .sql
        """
        self.sql_script(path_dbinserttables)
        return f"Таблицы БД {self.__db_name} успешно заполнены"

    def sql_script(self, path: str) -> None:
        """
        Считывание и запуск sql скрипта из файла .sql
        """
        try:
            conn = psycopg2.connect(dbname=self.__db_name, **self.__params)
            with conn:
                with conn.cursor() as cur:
                    cur.execute(self.sql_read(path))
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
            exit(1)

    @staticmethod
    def sql_read(path: str) -> str:
        """
        Чтение .sql файла.
        :param path: Путь к файлу, str.
        :return: sql-скрипт, str.
        """
        with open(path, 'r', encoding='utf-8') as sql:
            return sql.read()

    def __str__(self) -> str:
        return f'Создание БД {self.__db_name}, таблиц, заполнение справочных таблиц данными '

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__db_name}, host: {self.__params['host']}, port: {self.__params['port']})"