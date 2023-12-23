from loguru import logger

import psycopg2


class DBManager:
    def __init__(self, db_name: str, params: dict) -> None:
        self.__db_name = db_name
        self.__params = params

    def get_db(self, database_request: str, columns_list: list, log: str) -> list[dict]:
        """
        Получение списка словарей по SQL-запросу.
        :param database_request: SQL-запрос, str.
        :param columns_list: Список ключей словаря (полей таблицы БД), list.
        :param log: Лог выполненного запроса, str.
        :return: Список словарей по SQL-запросу, list[dict]
        """
        conn = psycopg2.connect(dbname=self.__db_name, **self.__params)
        try:
            with conn:
                with conn.cursor() as cur:
                    # Формируем запрос
                    cur.execute(database_request)
                    # Формируем список словарей
                    fetch = cur.fetchall()
                    result = []
                    for row in fetch:
                        result.append(dict(zip(columns_list, row)))
            logger.info(log)
            return result
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error(
                f'Получение данных данных по запросу ({self.__class__.__name__}): {error}')
            exit(1)
        finally:
            conn.close()

    def get_companies_and_vacancies_count(self) -> list[dict]:
        """
        Получает список всех компаний и количество вакансий у каждой из них.
        """
        database_request = ("SELECT employers.employer_name, COUNT(*), employer_id  FROM vacancies "
                            "INNER JOIN employers USING(employer_id) "
                            "GROUP BY employers.employer_name, employer_id "
                            "ORDER BY COUNT(*) DESC, employers.employer_name "
                            "LIMIT 10")
        columns_list = ['employer_name', 'count', 'employer_id']
        log = 'Данные о количестве вакансий в компаниях (ТОП-10) получены успешно'
        return self.get_db(database_request, columns_list, log)

    def get_all_vacancies(self):
        """
        Получает список всех вакансий с указанием названия компании,
        названия вакансии и зарплаты и ссылки на вакансию.
        """
        database_request = ("SELECT date_publication, position_employee, employers.employer_name, "
                            "salary_from, salary_to, currency.currency_name, "
                            "schedule.schedule_name, employment.employment_name, "
                            "experience.experience_name, applicant_requirements, duties, employer_address, url "
                            "FROM vacancies "
                            "INNER JOIN employers USING (employer_id) "
                            "INNER JOIN currency USING (currency_id) "
                            "INNER JOIN schedule USING (schedule_id) "
                            "INNER JOIN employment USING (employment_id) "
                            "INNER JOIN experience USING (experience_id) "
                            "ORDER BY date_publication desc, salary_from desc, employers.employer_name")
        columns_list = ['date_publication', 'position_employee', 'employer_name',
                        'salary_from', 'salary_to', 'currency_name', 'schedule_name',
                        'employment_name', 'experience_name', 'applicant_requirements',
                        'duties', 'employer_address', 'url']
        log = 'Данные обо всех вакансиях получены успешно'
        return self.get_db(database_request, columns_list, log)

    def get_avg_salary(self):
        """
        Получает среднюю зарплату по вакансиям (от и до)
        """
        database_request = ("SELECT avg(salary_from) as avg_salary FROM vacancies "
                            "WHERE salary_from > 0 "
                            "UNION ALL "
                            "SELECT avg(salary_to) as avg_salary FROM vacancies "
                            "WHERE salary_to > 0")
        columns_list = ['avg_salary']
        log = 'Данные о средней заработной плате (от и до)'
        return self.get_db(database_request, columns_list, log)

    def get_vacancies_with_higher_salary(self):
        """
        Получает список всех вакансий, у которых зарплата выше средней по всем вакансиям.
        """
        avg_salary_from = round(self.get_avg_salary()[0]['avg_salary'], 2)
        avg_salary_to = round(self.get_avg_salary()[1]['avg_salary'], 2)
        database_request = (f"SELECT date_publication, position_employee, employers.employer_name, "
                            f"salary_from, salary_to, currency.currency_name, "
                            f"schedule.schedule_name, employment.employment_name, "
                            f"experience.experience_name, applicant_requirements, duties, employer_address, url "
                            f"FROM vacancies "
                            f"INNER JOIN employers USING (employer_id) "
                            f"INNER JOIN currency USING (currency_id) "
                            f"INNER JOIN schedule USING (schedule_id) "
                            f"INNER JOIN employment USING (employment_id) "
                            f"INNER JOIN experience USING (experience_id) "
                            f"WHERE salary_from > {avg_salary_from} OR salary_to > {avg_salary_to} "
                            f"ORDER BY date_publication desc, salary_from desc, employers.employer_name")
        columns_list = ['date_publication', 'position_employee', 'employer_name',
                        'salary_from', 'salary_to', 'currency_name', 'schedule_name',
                        'employment_name', 'experience_name', 'applicant_requirements',
                        'duties', 'employer_address', 'url']
        log = 'Данные о вакансиях с зарплатой выше среднего получены успешно'
        return self.get_db(database_request, columns_list, log)

    def get_vacancies_with_keyword(self, word: str):
        """
        Получает список всех вакансий, в названии которых содержатся переданные в метод слова, например python.
        """
        database_request = (f"SELECT date_publication, position_employee, employers.employer_name, "
                            f"salary_from, salary_to, currency.currency_name, "
                            f"schedule.schedule_name, employment.employment_name, "
                            f"experience.experience_name, applicant_requirements, duties, employer_address, url "
                            f"FROM vacancies "
                            f"INNER JOIN employers USING (employer_id) "
                            f"INNER JOIN currency USING (currency_id) "
                            f"INNER JOIN schedule USING (schedule_id) "
                            f"INNER JOIN employment USING (employment_id) "
                            f"INNER JOIN experience USING (experience_id) "
                            f"WHERE position_employee ~~* '%{word}%' "
                            f"ORDER BY salary_from desc, date_publication desc")
        columns_list = ['date_publication', 'position_employee', 'employer_name',
                        'salary_from', 'salary_to', 'currency_name', 'schedule_name',
                        'employment_name', 'experience_name', 'applicant_requirements',
                        'duties', 'employer_address', 'url']
        log = 'Данные о вакансиях с зарплатой по ключевому слову получены успешно'
        return self.get_db(database_request, columns_list, log)

    def __str__(self) -> str:
        return 'Получение данных из БД vacancies'

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}. БД {self.__db_name}, host: {self.__params[0]}, port: {self.__params[3]}"
