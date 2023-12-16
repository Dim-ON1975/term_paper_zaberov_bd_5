import os
import psycopg2

from src.conf.config import config
from src.conf.constants import SCRIPT_DBCREATE, SCRIPT_DBCREATETABLES, SCRIPT_DBINSERTTABLES, DB_NAME
from src.utils.creationdb import CreationDB


def main():
    """Основной код программы"""
    params = config()

    db = CreationDB(params, DB_NAME)

    # Создание БД, таблиц, заполнение некоторых таблиц справочными данными
    db.create_database(SCRIPT_DBCREATE)
    db.create_tables(SCRIPT_DBCREATETABLES)
    db.insert_tables(SCRIPT_DBINSERTTABLES)


if __name__ == '__main__':
    main()
