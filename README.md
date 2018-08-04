# SSkey
REST application 

## Getting started

Install [docker](https://docs.docker.com/engine/installation/) and run:

```shell
docker-compose up
# docker-compose stop
```

Otherwise, for the standalone web service:

```shell
pip install -r requirements.txt
python manage.py
```

Visit [http://localhost:5000](http://localhost:5000)

## Flask Application Structure 

```

.
├── docker-compose.yml
├── README.md
└── src
    ├── app
    │   ├── base.py
    │   ├── config.py
    │   ├── errors
    │   │   ├── handlers.py
    │   │   └── __init__.py
    │   ├── __init__.py
    │   ├── migrate.py
    │   ├── models.py
    │   ├── requirements.txt
    │   ├── resources.py
    │   ├── routes.py
    │   ├── shemas.py
    │   └── swagger.yaml
    ├── boot.sh
    ├── Dockerfile
    ├── __init__.py
    ├── manage.py
    └── tests
        ├── __init__.py
        └── test_basic.py

```

## Development

Create a new branch off the **develop** branch for features or fixes.

After making changes rebuild images and run the app:

```shell
docker-compose build
docker-compose run -p 5000:5000 web python manage.py
```

## Tests

Standalone unit tests run with:

```shell
python -m pytest tests/
```

## Postgresql

Install [postgresql](https://www.postgresql.org/download/) and run:
```shell
python base.py # database config
python migrate.py # in order to create database
```
