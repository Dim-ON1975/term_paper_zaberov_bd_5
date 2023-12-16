import os

# URL регионы
URL_AREAS_HH = 'https://api.hh.ru/areas/113'
# id России для поиска вакансий
ID_RUSSIA_HH = 113

# SQL
DB_NAME = 'vacancies'
PATH_INI = os.path.join('..', 'src', 'conf', 'database.ini')
# Скрипты
# Создание БД, таблиц, заполнение таблиц
SCRIPT_DBCREATE = os.path.join('..', 'src', 'conf', 'dbcreate.sql')
SCRIPT_DBCREATETABLES = os.path.join('..', 'src', 'conf', 'dbcreatetables.sql')
SCRIPT_DBINSERTTABLES = os.path.join('..', 'src', 'conf', 'dbinserttables.sql')