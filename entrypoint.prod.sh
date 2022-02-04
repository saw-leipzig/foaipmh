#!/bin/sh

python manage.py migrate --noinput
python manage.py collectstatic --no-input
python manage.py shell --command "from oai_pmh.models import MetadataFormat; print(MetadataFormat.objects.get_or_create(prefix='cmdi', schema='https://infra.clarin.eu/CMDI/1.x/xsd/cmd-envelop.xsd', namespace='http://www.clarin.eu/cmd/1'))"

exec "$@"
