# django test environment

## project repository
https://github.com/Taze00/django

## commands

### Create a new Django project
docker compose run web-app django-admin startproject composeexample .
sudo chown -R $USER:$USER composeexample manage.py
sudo docker compose run web-app django-admin migrate

### start existing django project
docker compose up -d

### stop existing django project
docker compose down

### migrate  existing django project
docker compose run web-app python3 manage.py migrate

### start bash shell inside container
docker compose run web-app bash



## bookmarks

* https://github.com/docker/awesome-compose/blob/master/official-documentation-samples/django/README.md
