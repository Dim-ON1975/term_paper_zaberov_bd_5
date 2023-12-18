from src.conf.config import config
from loguru import logger

from src.conf.constants import LOG_AUTO, LOG_USER, UPDATE_DAYS
from src.utils.utils import log_json, read_logfile, create_database, update_desired


def main():
    """Основной код программы"""
    # Создание базы данных, если она не существует
    log_json()  # запись логов в файл
    params = config()  # параметры подключения к БД

    # Создание и заполнение БД
    create_database(params)

    days_after_last_update, date_after_last_update, flag_update = read_logfile()

    if flag_update and abs(days_after_last_update) >= UPDATE_DAYS:
        # Обновление данных в БД
        print(f'С момента последнего обновления прошло {days_after_last_update} дн.')
        update_desired(params)
        logger.info(LOG_AUTO)  # Лог: автоматическое обновление
    elif abs(days_after_last_update) > 1:
        select_update = int(input(f'Последнее обновление данных: {date_after_last_update}.\n'
                                  f'До автоматического обновления данных осталось: '
                                  f'{UPDATE_DAYS - abs(days_after_last_update)} дн.\n'
                                  f'  Продолжить без обновления - 0\n'
                                  f'  Обновить сейчас.......... - 1\n'
                                  f'  Введите команду: '))
        if select_update == 1:
            # Обновление данных в БД
            update_desired(params)
            logger.info(LOG_USER)  # Лог: обновление по требованию пользователя
        else:
            # Работа с имеющимися данными
            pass


if __name__ == '__main__':
    main()
