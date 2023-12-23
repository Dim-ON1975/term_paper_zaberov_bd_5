from configparser import ConfigParser

from src.conf.constants import PATH_INI


def config(filename: str = PATH_INI, section: str = "postgresql") -> dict:
    """
    Читает параметры в файле database.ini и возвращает их как словарь.
    :param filename: Имя файла, хранящего конфигурацию доступа к БД, str.
    :param section: Секция, содержащая данные в файле, str.
    :return: Словарь с параметрами БД, dict.
    """
    # Создание парсера.
    parser = ConfigParser()
    # Чтение файла конфигурации
    parser.read(filename)
    # Проверка наличия синтаксического анализатора секции (postgresql)
    if parser.has_section(section):
        params = parser.items(section)
        db = dict(params)
    else:
        # Возвращаем ошибку, если вызывается параметр, не указанный в файле инициализации
        raise Exception(f'Section {section} is not found in the {filename} file.')
    return db
