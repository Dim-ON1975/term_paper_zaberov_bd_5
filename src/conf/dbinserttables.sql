-- Заполнение данными таблицы "Валюта"
INSERT INTO currency(currency_name) VALUES
	('RUR'),
	('EUR'),
	('USD');


-- Заполнение данными таблицы "График работы"
INSERT INTO schedule(schedule_name) VALUES
    ('Вахтовый метод'),
    ('Гибкий график'),
    ('Полный день'),
    ('Сменный график');


-- Заполнение данными таблицы "Занятость"
INSERT INTO employment(employment_name) VALUES
    ('Полная занятость'),
    ('Проектная работа'),
    ('Частичная занятость');


-- Заполнение данными таблицы "Опыт работы"
INSERT INTO experience(experience_name) VALUES
    ('Нет опыта'),
    ('От 1 года до 3 лет'),
    ('От 3 до 6 лет'),
    ('Более 6 лет');