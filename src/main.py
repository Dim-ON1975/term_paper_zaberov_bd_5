from datetime import datetime

from src.conf.config import config

from src.utils.utils import log_json, create_database, update_desired, select_history, \
    print_companies_and_vacancies_count, print_all_vacancies, message_avg_salary, print_vacancies_with_higher_salary, \
    print_vacancies_with_keyword


def main():
    """Основной код программы"""
    # Создание базы данных, если она не существует
    log_json()  # запись логов в файл
    params = config()  # параметры подключения к БД

    # Создание и заполнение БД
    create_database(params)

    while True:
        # Получение данных об истории приложения
        history_datetime = select_history()[1]
        history_area = select_history()[2]

        # Прошло количество дней с момента последнего запроса
        date_update = history_datetime
        date_now = datetime.now().replace(microsecond=0)
        days_after_last_update = (date_now - date_update).days
        date_update_str = datetime.strftime(date_update, '%d.%m.%Y в %H:%M:%S')

        if abs(days_after_last_update) == 0:
            days = 'сегодня'
        else:
            days = str(abs(days_after_last_update)) + ' дн. назад'

        try:
            select_update = int(
                input(f'\nПоследнее обновление данных: {date_update_str} ({history_area.upper()}, {days}).\n'
                      f'  Продолжить без обновления - 0\n'
                      f'  Обновить сейчас.......... - 1\n'
                      f'  Выйти из программы....... - 3\n'
                      f'  Введите команду: '))
        except ValueError:
            select_update = 3

        if select_update >= 3 or select_update < 0:
            break

        if select_update == 1:
            # Обновление данных в БД
            update_desired(params)

        # Получение данных из БД
        # ТОП-10 компаний по количеству вакансий
        print_companies_and_vacancies_count()

        # Информация о средней зарплате по всем вакансиям
        print(message_avg_salary())

        try:
            select_print = int(
                input('Выберите один из пунктов:\n'
                      '  Все вакансии ........................ - 0\n'
                      '  Вакансии с зарплатой выше средней ... - 1\n'
                      '  Вакансии с поиском по ключевому слову - 3\n'
                      '  Выйти из программы .................. - 4\n'
                      '  Введите команду: '))
        except ValueError:
            select_print = 4

        if select_print >= 4 or select_print < 0:
            break

        if select_print == 0:
            # Вывод на экран выбранного количества вакансий или 10 (по-умолчанию)
            print_all_vacancies()

        if select_print == 1:
            # Вывод на экран вакансий с зарплатой выше средней или 10 (по-умолчанию)
            print_vacancies_with_higher_salary()

        if select_print == 3:
            # Вывод на экран вакансий по ключевому слову или 10 (по-умолчанию)
            print_vacancies_with_keyword()
    exit(0)


if __name__ == '__main__':
    main()
