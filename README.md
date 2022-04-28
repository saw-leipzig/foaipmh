# foaipmh
Fedora OAI-PMH Endpoint.

## Development
* Local config in `local.py`, see Settings section.
* If not otherwise configured and sqlite DB will be used.

* Run without Docker:
  * Create virtual environment and activate it and install dependencies:
    ```
    $ virtualenv -p /usr/bin/python3 .venv
    $ source .venv/bin/activate
    $ pip install -r requirements
    ```

  * Migrate database:

    ```$ python manage.py migrate```

    * Add CMDI MetadataFormat, see `entrypoint.prod.sh`.

  * Run Django dev server

    ```$ python manage.py runserver```

  * Run tests

    ```$ python manage.py tests```

* Run with Docker:
  * Install [Docker CE](https://docs.docker.com/install/) and [Docker Compose](https://docs.docker.com/compose/install/).
  * Run and build Docker image:

    ```$ docker-compose up --build```

## Production
* Local config in `local.py`, see Settings section.

* Run Docker container in detached mode:

  ```$ docker-compose up --build -d```


## Settings
* Local config in `local.py`:
  ```python
  TIME_ZONE = 'Europe/Berlin'
  ADMINS = [('NAME', 'EMAIL')]
  ALLOWED_HOSTS = ('localhost', '127.0.0.1') # For production set to ("DNS",)
  BASE_URL = "https://repo.data.saw-leipzig.de/oai-pmh"

  FEDORA_REST_ENDPOINT = "URL"
  FEDORA_AUTH = ("USERNAME", "PASSWORD") # or None
  FEDORA_METADATA_PREDICATES = {
      # OAI-PMH metadata format prefix: metadata record predicate
      "cmdi": "http://saw-leipzig.de/vocabulary#cmdiRecord",
      "oai_dc": "http://saw-leipzig.de/vocabulary#dcmiRecord"
  }

  OAI_PMH = {
      "REPOSITORY_NAME": "SAW Leipzig",
      "NUM_PER_PAGE": 200 # Default 100
  }
  ```

* Additionally, for production:
  ```python
  DEBUG = False

  DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "DB NAME",
        "USER": "DB USER",
        "PASSWORD": "DB PASSWORD",
        "HOST": "db", # Docker service name or URL/IP
        "PORT": 5432,
    }
  }
  ```
* **Docker**: for the DB create `.env.db` file with same info as in `local.py`:
  ```
  POSTGRES_USER=DB USER
  POSTGRES_PASSWORD=DB PASSWORD
  POSTGRES_DB=DB NAME
  ```
* OAI-PMH:
  * For the adminEmail-Tags the Email-Addresses from the `ADMINS` will be taken.
  * For the baseURL-Tag the first entry in `ALLOWED_HOSTS` will be taken.
* [Django settings reference](https://docs.djangoproject.com/en/3.1/ref/settings/)


## Import

To import data from Fedora run:

```$ python manage.py import```

or with docker:

```$ docker-compose exec web python manage.py import```

Arguments:
* `-s`/`--sleep`: Sleep between request to prevent timeout, default 5 (sec).
* `-v {0,1,2,3}`/`--verbosity {0,1,2,3}`: Verbosity level, default 1, for cron set to 0.

## Endpoints

* `oai2/`: OAI-PMH endpoint
* `admin/`: Django admin interface
  * Users can be created with:

    ```$ python manage.py createsuperuser```
