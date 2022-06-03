# foaipmh
A Fedora 6 OAI-PMH endpoint, originally by [jnphilipp](https://github.com/jnphilipp) and based on his 
[Django OAI-PMH app](https://github.com/jnphilipp/django_oai_pmh). <br>

`Foaipmh` will harvest metadata via the REST-API of a Fedora 6 repository and provide an OAI-PMH-compliant endpoint. By default, 
CMDI and DCMI metadata are harvested and served but additional formats can be added via configuration.<br>

**Note:** Currently, the harvesting process is a straightforward depth-first traversal of all resources in the 
repository - and therefore not particularly optimized or efficient. Especially for large repositories, this means 
harvesting could take time and result in a lot of calls to the REST-API. We plan on optimizing this process in the
future.


## Setup & Usage (Production)

### Configuration
* Create a local config in `local.py`, filling/changing relevant fields, which includes 
 [Django](https://www.djangoproject.com/) settings and configuration specific to `Foaipmh`:
  ```python
  TIME_ZONE = 'Europe/Berlin'
  ADMINS = [('NAME', 'EMAIL')]
  ALLOWED_HOSTS = ('localhost', '127.0.0.1')

  FEDORA_REST_ENDPOINT = "URL"
  FEDORA_AUTH = ("USERNAME", "PASSWORD") # or None
  
  FEDORA_METADATA_PREDICATES = {
      # OAI-PMH metadata format prefix: metadata record predicate
      "cmdi": "https://example.org/vocabulary#cmdiRecord",
      "oai_dc": "https://example.org/vocabulary#dcmiRecord"
  }

  OAI_PMH = {
      "REPOSITORY_NAME": "REPO_NAME",
      "NUM_PER_PAGE": 200, # Default 100
      "BASE_URL": "https://example.org/"
  }
  
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


* [Django settings reference](https://docs.djangoproject.com/en/3.1/ref/settings/)


* `FEDORA_METADATA_PREDICATES` tells the harvester which predicates in the Fedora 6 repository correspond with which 
 metadata format. This includes CMDI and DCMI by default, **for which predicates have to be specified.** <br>
 Additional metadata formats can be added here as well, with the pattern `"FORMAT_PREFIX": "PREDICATE"`. Note that this also
 entails an additional step after installation, see **Usage**.


* For the Docker-internal DB create an `.env.db` file with same info as in `local.py`:
  ```
  POSTGRES_USER=DB USER
  POSTGRES_PASSWORD=DB PASSWORD
  POSTGRES_DB=DB NAME
  ```
  
* OAI-PMH notes:
  * For the adminEmail-Tags the Email-Addresses from the `ADMINS` will be taken.
  * For the baseURL-Tag the `BASE_URL` parameter in `OAI_PMH` is used.

### Installation
  * Install [Docker CE](https://docs.docker.com/install/) and [Docker Compose](https://docs.docker.com/compose/install/).

  * Build and run a Docker container in detached mode:

    ```$ docker-compose up --build -d```

### Usage
* To **import data** from the Fedora 6 repository, run:<br>
```$ docker-compose exec web python manage.py import```<br><br>
**Arguments:**
  * `-s`/`--sleep`: Sleep between request to prevent timeout, default 5 (sec).
  * `-v {0,1,2,3}`/`--verbosity {0,1,2,3}`: Verbosity level, default 1, for cron set to 0.


* (**Optional**) To designate additional metadata formats for harvesting (besides CMDI/DCMI), make a copy of
`entrypoint.prod.sh`, but change the values of `prefix`, `schema` and `namespace` to the new format values. 
 Then execute the file via:<br>
```docker-compose exec web sh copied_file.sh``` <br>
This also requires the format prefix and its corresponding predicate being added in the `local.py`
file during configuration (see **Configuration** above).

### Endpoints

* `oai2/`: OAI-PMH endpoint
* `admin/`: Django admin interface
  * Users can be created with:
    ```$ python manage.py createsuperuser```


## Setup & Usage (Development)

### Configuration
* Create a local config in `local.py` similar to production, just omit `DEBUG` and `DATABASES`.

* If not otherwise configured a sqlite DB will be used in development mode.

### Installation (non-dockerized)
* To run without Docker:
  * Create virtual environment and activate it and install dependencies:
    ```
    $ virtualenv -p /usr/bin/python3 .venv
    $ source .venv/bin/activate
    $ pip install -r requirements
    ```

  * Migrate database:

    ```$ python manage.py migrate```

    * Add CMDI MetadataFormat, see `entrypoint.prod.sh`.

* (For dockerized usage, the `.env.db` config file is needed, see **Production Installation**)

### Usage (non-dockerized)

  * Run Django dev server

    ```$ python manage.py runserver```

  * Run tests

    ```$ python manage.py tests```