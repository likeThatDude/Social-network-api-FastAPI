# **Twitter Clone**
## Description
Twitter Clone is a web application that mimics the basic functions of Twitter, 
such as posting tweets, subscribing to users, and browsing the news feed.

## Technologies
- Backend: FastApi, Celery, Flower, Sentry, Alembic, S3, SQLAlchemy, Nginx
- Database: PostgreSQL, Redis
- Authentication: Basic Authentication

## Operating Principle
#### ***Client Area***
There are two main pages:
- Main page with all tweets


![Main page](https://s3.timeweb.cloud/ff09e896-6380cf4a-95c7-4b26-ad18-d0aef6f07a91/readme_files/mian_page.png)
- User page


![User page](https://s3.timeweb.cloud/ff09e896-6380cf4a-95c7-4b26-ad18-d0aef6f07a91/readme_files/user_page.png)
- Authorization, by assignment, is implemented chezer header that is sent when the user requests the server, setting the value of the
is set by entering the key in a special field:


![auth page](https://s3.timeweb.cloud/ff09e896-6380cf4a-95c7-4b26-ad18-d0aef6f07a91/readme_files/auth.png)


This field is constantly shown on the main page.
Initially there are two users in the database: **test, test1**

- Users can leave tweets both with text and add pictures to their tweets,
It is provided that the user can upload only pictures with a certain extension (all the basic ones are available).

- Users can give each other likes, subscribe to each other.

#### ***Server Part***
- When an image is uploaded, if it is large it is compressed to a lower resolution and lower weight.
Here is an example of such compression:


![comp pic](https://s3.timeweb.cloud/ff09e896-6380cf4a-95c7-4b26-ad18-d0aef6f07a91/readme_files/compress.jpeg)
- All media files are stored on a private S3 storage.
- All logs are stored in text files, their rotation is implemented, followed by compression into archive. 
old logs and sending these archives to S3 storage.
- It is also provided to create database dumps to prevent data loss.
Dumps are made every hour, once a day and once a week.
All dumps are also sent to S3 storage, everything is organized in folders.
- Old logs and dumps are removed from the container, to prevent the weight of the folders with them from growing.
- The S3 repository has ***lifecycle rules*** with specific retention times for each 
types of dumps and logs separately.
- All of the above processes are ***automated*** and do not require user involvement.
- Most of the data in the application is hashed to prevent heavy load on the database.
The data hash is not passed to the browser, so that the user always has an up-to-date feed of tweets.
This is done due to the peculiarities of the TOR and WebSockets are not used here.

#### ***Tests***
The project is covered with unit and integration tests, using pytest.


![tests](https://s3.timeweb.cloud/ff09e896-6380cf4a-95c7-4b26-ad18-d0aef6f07a91/readme_files/test.png)

## Installation

1. Clone the repository:
```bash
   git clone git@github.com:likeThatDude/Twitter_clone.git
```
2. Navigate to the folder with the application
3. Execute the command
```bash
   docker compose up
```


## Customization
- Create an .env file in the root folder of the project.
- Insert and fill the following empty variables with your data:

MODE=PROD change to TEST for testing

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


# Developer
**Gorbatenko Ivan**

**GitHub**: https://github.com/likeThatDude  

**Email**: 1995van95@gmail.com