-- Таблица "Регионы, города/населённые пункты"
CREATE TABLE IF NOT EXISTS areas
(
    area_id integer NOT NULL,
    area_name varchar(100) NOT NULL,

    CONSTRAINT pk_areas_area_id PRIMARY KEY (area_id)
);

-- Таблица "Работодатели"
CREATE TABLE IF NOT EXISTS employers
(
    employer_id serial NOT NULL,
    area_id integer NOT NULL,
    employer_name varchar(200) NOT NULL,

    CONSTRAINT pk_employers_employer_id PRIMARY KEY (employer_id),
    CONSTRAINT fk_employers_area_id FOREIGN KEY (area_id) REFERENCES areas(area_id)
);


-- Таблица "Валюта"
CREATE TABLE IF NOT EXISTS currency
(
    currency_id serial NOT NULL,
    currency_name varchar(3) NOT NULL,

    CONSTRAINT pk_currency_currency_id PRIMARY KEY (currency_id)
);

-- Таблица "График работы"
CREATE TABLE IF NOT EXISTS schedule
(
    schedule_id serial NOT NULL,
    schedule_name varchar(50) NOT NULL,

    CONSTRAINT pk_schedule_schedule_id PRIMARY KEY (schedule_id)
);

-- Таблица "Занятость"
CREATE TABLE IF NOT EXISTS employment
(
    employment_id serial NOT NULL,
    employment_name varchar(50) NOT NULL,

    CONSTRAINT pk_employment_employment_id PRIMARY KEY (employment_id)
);

-- Таблица "Опыт работы"
CREATE TABLE IF NOT EXISTS experience
(
    experience_id serial NOT NULL,
    experience_name varchar(50) NOT NULL,

    CONSTRAINT pk_experience_experience_id PRIMARY KEY (experience_id)
);

-- Таблица "Отобранные вакансии"
CREATE TABLE IF NOT EXISTS vacancies
(
    vacancy_id serial NOT NULL,
    date_publication date NOT NULL,
    position_employee varchar(200) NOT NULL,
    employer_id integer NOT NULL,
    salary_from integer DEFAULT NULL,
    salary_to integer DEFAULT NULL,
    currency_id integer NOT NULL,
    schedule_id integer NOT NULL,
    employment_id integer NOT NULL,
    experience_id integer NOT NULL,
    applicant_requirements text DEFAULT NULL,
    duties text DEFAULT NULL,
    employer_address varchar(300) DEFAULT NULL,
    url varchar(200),

    CONSTRAINT pk_vacancies_vacancy_id PRIMARY KEY (vacancy_id),
    CONSTRAINT fk_vacancies_employer_id FOREIGN KEY (employer_id) REFERENCES employers(employer_id),
    CONSTRAINT fk_vacancies_currency_id FOREIGN KEY (currency_id) REFERENCES currency(currency_id),
    CONSTRAINT fk_vacancies_schedule_id FOREIGN KEY (schedule_id) REFERENCES schedule(schedule_id),
    CONSTRAINT fk_vacancies_employment_id FOREIGN KEY (employment_id) REFERENCES employment(employment_id),
    CONSTRAINT fk_vacancies_experience_id FOREIGN KEY (experience_id) REFERENCES experience(experience_id)
);

-- Таблица "История"
CREATE TABLE IF NOT EXISTS history
(
    history_id serial NOT NULL,
    history_datetime TIMESTAMP NOT NULL,
    history_area varchar(100) NOT NULL,

    CONSTRAINT pk_history_history_id PRIMARY KEY (history_id)
);