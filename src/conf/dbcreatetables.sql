-- Таблица "Регионы и города федерального значения (Москва, Санкт-Петербург)"
CREATE TABLE IF NOT EXISTS regions
(
    region_id integer NOT NULL,
    region_name varchar(100) NOT NULL,

    CONSTRAINT pk_regions_region_id PRIMARY KEY (region_id)
);

-- Таблица "Города/населённые пункты"
CREATE TABLE IF NOT EXISTS cities
(
    city_id integer NOT NULL,
    region_id integer NOT NULL,
    city_name varchar(100) NOT NULL,

    CONSTRAINT pk_cities_cities_id PRIMARY KEY (city_id),
    CONSTRAINT fk_cities_region_id FOREIGN KEY (region_id) REFERENCES regions(region_id)

);

-- Таблица "Работодатели"
CREATE TABLE IF NOT EXISTS employers
(
    employer_id serial NOT NULL,
    region_id integer NOT NULL,
    city_id integer NOT NULL,
    employer_name varchar(200) NOT NULL,
    employer_address varchar(300) DEFAULT NULL,

    CONSTRAINT pk_employers_employer_id PRIMARY KEY (employer_id),
    CONSTRAINT fk_employers_region_id FOREIGN KEY (region_id) REFERENCES regions(region_id),
    CONSTRAINT fk_employers_city_id FOREIGN KEY (city_id) REFERENCES cities(city_id)
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
    url varchar(200),

    CONSTRAINT pk_vacancies_vacancy_id PRIMARY KEY (vacancy_id),
    CONSTRAINT fk_vacancies_employer_id FOREIGN KEY (employer_id) REFERENCES employers(employer_id),
    CONSTRAINT fk_vacancies_currency_id FOREIGN KEY (currency_id) REFERENCES currency(currency_id),
    CONSTRAINT fk_vacancies_schedule_id FOREIGN KEY (schedule_id) REFERENCES schedule(schedule_id),
    CONSTRAINT fk_vacancies_employment_id FOREIGN KEY (employment_id) REFERENCES employment(employment_id),
    CONSTRAINT fk_vacancies_experience_id FOREIGN KEY (experience_id) REFERENCES experience(experience_id)
);