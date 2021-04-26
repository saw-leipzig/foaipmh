#!/bin/sh

python manage.py migrate --noinput
python manage.py collectstatic --no-input
python manage.py shell --command "from oai_pmh.models import MetadataFormat; print(MetadataFormat.objects.get_or_create(prefix='oai_cmdi', schema='http://www.clarin.eu/cmd/1', namespace='https://catalog.clarin.eu/ds/ComponentRegistry/rest/registry/1.x/profiles/clarin.eu:cr1:p_1527668176047/xsd'))"

exec "$@"
