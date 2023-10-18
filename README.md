# praktikum_new_diplom
## Foodgram
сайт, на котором пользователи будут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Пользователям сайта также будет доступен сервис «Список покупок». Он позволит создавать список продуктов, которые нужно купить для приготовления выбранных блюд.

## Для локального запуска проекта виртуальное окружение, установите в него зависимости из backend/requirements.txt и запустите контнейнеры командой -  docker compousu up.
В корневой директории создать файл .env и заполнить своими данными по аналогии:
POSTGRES_USER=user_name
POSTGRES_PASSWORD=password
POSTGRES_DB=django_db_name
DB_HOST=dbf
DB_PORT=5432
SECRET_KEY='секретный ключ Django'
DEBUG=False


## Для запуска на удаленном сервере.
Развернуть проект на удаленном сервере:
Клонировать репозиторий:
https://github.com/alinaPopad/foodgram-project-react.git
Установить на сервере Docker, Docker Compose:
sudo apt install curl                                   # установка утилиты для скачивания файлов
curl -fsSL https://get.docker.com -o get-docker.sh      # скачать скрипт для установки
sh get-docker.sh                                        # запуск скрипта
sudo apt-get install docker-compose-plugin              # последняя версия docker compose
Скопировать на сервер файл- docker-compose.production.yml
Для работы с GitHub Actions необходимо в репозитории в разделе Secrets > Actions создать переменные окружения:
SECRET_KEY              # секретный ключ Django проекта
DOCKER_PASSWORD         # пароль от Docker Hub
DOCKER_USERNAME         # логин Docker Hub
HOST                    # публичный IP сервера
USER                    # имя пользователя на сервере
PASSPHRASE              # *если ssh-ключ защищен паролем
SSH_KEY                 # приватный ssh-ключ

Создать и запустить контейнеры Docker, выполнить команду на сервере (версии команд "docker compose" или "docker-compose" отличаются в зависимости от установленной версии Docker Compose):
sudo docker compose up -d
После успешной сборки выполнить миграции:
sudo docker compose exec backend python manage.py migrate
Создать суперпользователя:
sudo docker compose exec backend python manage.py createsuperuser
Собрать статику:
sudo docker compose exec backend python manage.py collectstatic
Наполнить базу данных содержимым из файла ingredients.json:
sudo docker compose exec backend python manage.py load_ingredients.py


## Используемые библиотеки:
asgiref==3.7.2
certifi==2023.7.22
cffi==1.15.1
charset-normalizer==3.2.0
cryptography==41.0.3
defusedxml==0.7.1
Django==4.2.5
django-cors-headers==3.13.0
django-filter==23.2
django-templated-mail==1.1.1
djangorestframework==3.14.0
djangorestframework-simplejwt==5.3.0
djoser==2.2.0
drf-yasg==1.21.7
idna==3.4
inflection==0.5.1
oauthlib==3.2.2
packaging==23.1
Pillow==10.0.0
psycopg2-binary==2.9.7
pycparser==2.21
PyJWT==2.8.0
python3-openid==3.2.0
pytz==2023.3.post1
PyYAML==6.0.1
reportlab==4.0.4
requests==2.31.0
requests-oauthlib==1.3.1
six==1.16.0
social-auth-app-django==5.3.0
social-auth-core==4.4.2
sqlparse==0.4.4
typing_extensions==4.7.1
tzdata==2023.3
uritemplate==4.1.1
urllib3==2.0.4


## Автор

- Попадченко Алина 

Для ревью:
https://taski2023.ddns.net/
84.201.154.246
admin: alina@alina.com
password: alina
