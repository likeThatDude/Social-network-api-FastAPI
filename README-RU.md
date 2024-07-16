
# **Twitter Clone**

## Описание
Twitter Clone - это веб-приложение, которое имитирует основные функции Твиттера, 
такие, как публикация твитов, подписка на пользователей и просмотр ленты новостей.

## Технологии
- Backend: FastApi, Celery, Flower, Sentry, Alembic, S3, SQLAlchemy, Nginx
- База данных: PostgreSQL, Redis
- Аутентификация: Basic Authentication


## Принцип работы
#### ***Клиентская часть***
Есть две основные страницы:
- Главная страница со всеми твитами
  
![Main page](https://s3.timeweb.cloud/ff09e896-6380cf4a-95c7-4b26-ad18-d0aef6f07a91/readme_files/mian_page.png)
- Страница пользователя
  
![User page](https://s3.timeweb.cloud/ff09e896-6380cf4a-95c7-4b26-ad18-d0aef6f07a91/readme_files/user_page.png)

- Авторизация, по заданию, реализована чезер хедер который отправляется при запросе пользователя на сервер, установка значения
происходит при вводе ключа в специальное поле:

![auth page](https://s3.timeweb.cloud/ff09e896-6380cf4a-95c7-4b26-ad18-d0aef6f07a91/readme_files/auth.png)

Это поле постоянно показывается на главное странице.
Изначально в бд забиты два пользователя: **test, test1**

- Пользователи могут оставлять твиты как с текстом так и добавлять картинки к своим твитам,
предусмотрено чтобы пользователь мог загрузить только картинки с определённым расширением (все основные есть).

- Пользователи могут ставить друг другу лайки, подписываться друг на друга.

#### ***Серверная часть***
- Загрузка изображения, если оно большое происходит его сжатие до более низкого разрешения и меньшего веса.
Вот пример такого сжатия:
![comp pic](https://s3.timeweb.cloud/ff09e896-6380cf4a-95c7-4b26-ad18-d0aef6f07a91/readme_files/compress.jpeg)
- Все медиа файлы храняться на уалённом S3 хранилище.
- Все логи храняться в текстовых файлах, реализованная их ротация с последующим сжатием в архив 
старых логов и отправки этих архивов в S3 хранилище.
- Также предусмотрено создание дампов базы для предотвращения потери данных.
Дампы делаются каждый час, один раз в день и один раз в неделю.
Все дампы также отправляются в S3 хранилище, все распределено по папкам.
- Старые логи и дампы удаляются с контейнера, для предотвращения разрастания веса папок с ними.
- В S3 хранилище устанавливаются ***правила жизненного цикла*** с определённым временем хранением для каждого 
вида дампов и логов отдельно.
- Все выше перечисленные процессы ***автоматизированны*** и не требуют участия пользователя.
- Большая часть данных в приложении хешируется для предотвращения большой нагрузки на БД.
Хеш данных не передаётся в браузер, для того чтобы у пользователя была всегда актуальная лента твитов.
Это сделанно из-за особенностей ТЗ и ВебСокеты тут не применяются.

#### ***Тесты***
Проект покрыт юнит и интеграционными тестами, при помощи pytest.

![tests](https://s3.timeweb.cloud/ff09e896-6380cf4a-95c7-4b26-ad18-d0aef6f07a91/readme_files/test.png)

## Установка

1. Клонируйте репозиторий:
```bash
   git clone git@github.com:likeThatDude/Twitter_clone.git
```
2. Перейдите в папку с приложением
3. Выполните команду
```bash
   docker compose up
```

## Настройка
- Создайте .env файл в корневой папке проекта.
- Вставьте и заполните своими данными следующие пустые переменные:

MODE=PROD изминить на TEST для тестирования

##### Backup dir in app
BACKUP_DIR=backup_database

##### Logs dir in app
LOGS_DIR=logs

##### Postgres settings
DB_USER=postgres

DB_PASS=postgres

DB_NAME=postgres

##### S3 settings
S3_URL=

S3_BUCKET_NAME=

S3_ACCESS_KEY=

S3_SECRET_KEY=

S3_TWEETS_MEDIA_FOLDER=tweets_media/

S3_LOGS_FOLDER=logs

S3_DUMP_FOLDER=backup_database

S3_HOUR_FOLDER=hour_dumps

S3_DAY_FOLDER=day_dumps

S3_WEEK_FOLDER=week_dumps


##### Sentry settings
SENTRY_DSN=


##### Redis cache name setting
REDIS_TWEETS_CACHE=tweets_cache

REDIS_USER_CACHE=user_cache

##### Container names for Docker configuration
DOCKER_CLIENT=client

DOCKER_CLIENT_PORT=80

DOCKER_SERVER=server

DOCKER_SERVER_PORT=8000

DOCKER_DATABASE=postgresql

DOCKER_DATABASE_PORT=5432

DOCKER_REDIS=redis

DOCKER_REDIS_PORT=6379

REDIS_DB_CACHE=0

REDIS_CELERY=1

DOCKER_CELERY=celery

DOCKER_FLOWER=flower

DOCKER_FLOWER_PORT=5555

---

# Разработчик
**Горбатенко Иван**

**GitHub**: https://github.com/likeThatDude  

**Email**: 1995van95@gmail.com
