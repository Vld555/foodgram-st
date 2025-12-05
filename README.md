# Запуск проекта
## Шаг 1. Подготовка конфигурации (.env)
Создайте файл .env в infra/
Вставьте в него следующий текст (можете изменить пароли на свои):
### Настройки базы данных PostgreSQL
```
POSTGRES_DB=foodgram
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_HOST=db
DB_PORT=5432
```

### Настройки Django
```
SECRET_KEY='django-insecure-change-me-please'
DEBUG=False
ALLOWED_HOSTS=localhost 127.0.0.1 [::1] backend
```

## Шаг 2. Запуск контейнеров
Все команды выполняются из терминала, находясь в папке infra/.

Сборка и запуск. Эта команда скачает образы, соберет бэкенд и фронтенд, и запустит всё в фоновом режиме:
```docker-compose up -d --build```

## Шаг 3. Настройка Бэкенда (Выполняется один раз)

Теперь, когда сервер работает, нужно "настроить" его внутренности: создать таблицы в базе данных и загрузить статику.
Мы будем выполнять команды внутри работающего контейнера backend.
Создание миграций:
```
docker-compose exec backend python manage.py makemigrations
```
Применение миграций:
```
docker-compose exec backend python manage.py migrate
```
Сбор статики:
```docker-compose exec backend python manage.py collectstatic --no-input```

Загрузка ингредиентов
```docker-compose exec backend python manage.py load_ingredients```
Создание администратора:
```docker-compose exec backend python manage.py createsuperuser```

## Шаг 4. Проверка работы

Теперь проект полностью готов к работе.

Главная страница: Откройте в браузере ```http://localhost```.

Админка: ```http://localhost/admin/```

API Документация: ```http://localhost/api/docs/```.


Остановить проект:
```docker-compose stop```

Запустить снова (без пересборки):

```docker-compose up -d```
Посмотреть логи (если что-то сломалось):

```docker-compose logs -f```
