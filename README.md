# Proobrazovanie

Веб-платформа **Proobrazovanie** — это современное образовательное решение для преподавателей и студентов, позволяющее организовать взаимодействие, хранение и управление учебными материалами. Проект ориентирован не только на демонстрацию технологий, но и на реальное применение: он представляет собой полноценное веб-приложение, развернутое на сервере под управлением Linux.

---

## 🚀 Описание проекта

**Proobrazovanie** — это образовательная веб-платформа, созданная для упрощения работы учителей и студентов.  
Функционал позволяет:

- хранить учебные материалы;
- управлять доступом через систему аутентификации;
- выполнять операции с данными (CRUD) через базу MySQL;
- осуществлять быстрый поиск по контенту;
- работать в защищённой среде с учётом современных требований к веб-приложениям.

Разработка ведётся в команде под эгидой **Listara Company**. Я выступил в роли **full-stack разработчика**, реализовав серверную часть на Flask, спроектировав базу данных MySQL, подготовив серверную инфраструктуру и разработав шаблоны для фронтенда.

---

## ✨ Основные возможности

- 🔑 **Аутентификация пользователей** (регистрация, вход, роли).
- 📚 **CRUD-операции** с учебным контентом (создание, редактирование, удаление, просмотр).
- 🔎 **Поиск по базе данных** для быстрого доступа к материалам.
- 🌐 **Развёртывание на Linux-сервере** (Ubuntu).
- 🎨 **Адаптивные шаблоны на HTML/CSS** для удобного взаимодействия.

---

## 🛠️ Технологический стек

- **Backend:** [Python](https://www.python.org/), [Flask](https://flask.palletsprojects.com/)  
- **Database:** [MySQL](https://www.mysql.com/)  
- **Frontend:** HTML, CSS  
- **Deployment:** Linux (Ubuntu Server)  
- **Version Control:** Git  

---

## ⚙️ Установка и настройка

Ниже приведены шаги для запуска проекта в среде Linux (Ubuntu).  

### 1. Клонирование репозитория

```bash
git clone https://github.com/Playershut/Proobrazovanie.git
cd Proobrazovanie
````

### 2. Создание виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Настройка базы данных MySQL

1. Запустите MySQL:

   ```bash
   sudo service mysql start
   ```

2. Создайте базу данных:

   ```sql
   CREATE DATABASE proobrazovanie CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

3. Создайте пользователя и выдайте права:

   ```sql
   CREATE USER 'pro_user'@'localhost' IDENTIFIED BY 'your_password';
   GRANT ALL PRIVILEGES ON proobrazovanie.* TO 'pro_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

4. Выполните миграции/инициализацию схемы (замените на актуальные команды после добавления файлов миграций):

   ```bash
   # пример — изменить по ситуации
   flask db upgrade
   ```

### 5. Запуск приложения

```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

Приложение будет доступно по адресу: [http://localhost:5000](http://localhost:5000)

---

## 📂 Структура проекта

```bash
Proobrazovanie/
├── app/                  # Основная логика приложения
│   ├── models/           # Модели базы данных
│   ├── routes/           # Маршруты Flask
│   ├── templates/        # HTML-шаблоны
│   ├── static/           # Статические файлы (CSS, изображения)
│   └── __init__.py
├── requirements.txt      # Зависимости Python
├── config.py             # Конфигурация проекта
├── app.py                # Точка входа Flask
└── README.md             # Документация
```

---

## 📬 Контакты

Команда: **Listara Company**
Роль: Full-stack developer — Артур Аминов
GitHub: [Playershut](https://github.com/Playershut)
Email: player15hut@gmail.com
