# Foodgram

**Foodgram** — это социальная площадка для любителей готовить

---

## Технологии

* **Язык**: Python 3.10
* **Фреймворк**: Django 4.2.5
* **API**: Django REST Framework (DRF)
* **Аутентификация**: Djoser
* **Docker**: Docker Compose (для контейнеризации)
* **Веб-сервер**: Gunicorn + Nginx (Production)

---

## О проекте

Foodgram предоставляет следующие возможности:

- **Публикация рецептов**. Пользователи загружают изображения блюд, указывают название, ингредиенты и текстовое описание приготовления
- **Ингредиенты и количество**. Каждый рецепт хранит перечень ингредиентов с единицами измерения и нужным количеством
- **Избранное и список покупок**. Пользователь может помечать рецепты «избранными» и добавлять их в свой список покупок
- **Подписки на авторов**. Подписка на других пользователей позволяет быстро просматривать их новые рецепты
- **Короткие ссылки на рецепт**. Генерация уникальных кодов для быстрого перехода к рецепту через специальный URL
- **REST API**. Вся логика реализована через DRF (Django REST Framework), что позволяет подключать мобильные и веб-приложения


---

## Инструкция по развёртыванию

### Локальная разработка

1. **Клонирование репозитория**  
   ```bash
   git clone https://github.com/evg1111/foodgram-st.git
   cd foodgram/backend
    ```

2. **Создание и активация виртуального окружения**

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux / macOS
   source venv/bin/activate
   ```

3. **Установка зависимостей**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Настройка переменных окружения**
   Создайте файл `.env` в infra и добавьте в него ключи
   Пример:

   ```dotenv
   SECRET_KEY=1
   DEBUG=True
   ALLOWED_HOSTS=127.0.0.1,localhost,*
   ```

5. **Применение миграций**

   ```bash
   python manage.py migrate
   ```

6. **Запуск локального сервера**

   ```bash
   python manage.py runserver
   ```

7. **Создание суперпользователя (опционально)**

   ```bash
   python manage.py createsuperuser
   ```

8. **Тестирование API**
   Перейдите в браузере по адресу:

   ```
   http://127.0.0.1:8000/api/
   ```

   Здесь доступны все эндпоинты (регистрация, авторизация, рецепты, подписки, избранное и т.д.).

### Запуск в Docker

1. **Перейти в папку `infra`:**
   ```bash
   cd infra


2. **Создать файл `.env`** (рядом с `docker-compose.yml`) и вставить:

   ```dotenv
   SECRET_KEY=your-secret-key-here
   DEBUG=False
   ALLOWED_HOSTS=localhost,127.0.0.1,backend
   ```

3. **Убедиться, что в `docker-compose.yml` прописаны сервисы `web` и `nginx`, а у `web` указан контекст с `Dockerfile` (обычно `context: ..`).**

4. **Собрать образы и запустить контейнеры:**

   ```bash
   docker compose up --build
   ```

   * `--build` — пересобирает образ `web`, если что-то поменялось в коде или зависимостях.
   * По умолчанию контейнеры стартуют в фоновом режиме.

5. **Проверить, что все сервисы запустились:**

   ```bash
   docker compose ps
   ```

   Ожидается состояние `Up` для:

   * `infra_web` (Django + Gunicorn)
   * `infra_nginx` (Nginx)

6. **(Опционально) Создать суперпользователя для Django:**

   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

7. **Остановка контейнеров:**

   ```bash
   docker compose down
   ```

   Если нужно удалить тома (БД, статика, медиа):

   ```bash
   docker compose down -v
   ```

Теперь проект полностью развёрнут в Docker


---

## Автор

* **ФИО**: Евгений
* **GitHub**: [github.com/evg1111](https://github.com/evg1111)
* **Telegram**: [@evgen1yg](https://t.me/evgen1yg)

---

Cсылка на github: https://github.com/evg1111/foodgram-st.git
