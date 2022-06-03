"""Fedora OAI-PMH Django app import command."""

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from django.conf import settings
from django.core.management.base import BaseCommand
from django_oai_pmh.models import Header, MetadataFormat, Set, XMLRecord
from time import sleep
from xml.etree import ElementTree


class Command(BaseCommand):
    """Fedora OAI-PMH import command."""

    help = "Import metadata from Fedora."

    key_set_spec = "http://www.openarchives.org/OAI/2.0/setSpec"
    key_set_name = "http://www.openarchives.org/OAI/2.0/setName"
    key_identifier = "http://purl.org/dc/elements/1.1/identifier"
    key_created = "http://fedora.info/definitions/v4/repository#created"
    key_memberof = "http://purl.org/dc/elements/1.1/memberOf"
    sets = {}

    def add_arguments(self, parser):
        """Add arguments."""
        parser.add_argument(
            "-s",
            "--sleep",
            type=int,
            default=5,
            help="Sleep interval in sec. To prevent too many requests in short time. "
            + "Default: 5",
        )

    def handle(self, *args, **options):
        """Handle command."""
        verbosity = int(options["verbosity"])

        metadata_formats = {}
        for k, v in settings.FEDORA_METADATA_PREDICATES.items():
            try:
                metadata_formats[k] = MetadataFormat.objects.get(prefix=k)
            except MetadataFormat.DoesNotExist as e:
                self.stderr.write(
                    self.style.ERROR(
                        f'Missing metadata format for "{k}" Fedora metadata suffix.'
                    )
                )
                self.stdout.write(self.style.ERROR(e))

        if verbosity >= 1:
            self.stdout.write(f"Import metadata from {settings.FEDORA_REST_ENDPOINT}.")

        nb_sets = Set.objects.count()
        nb_headers = Header.objects.count()

        self.sets = {}

        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=1.0)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        self.fetch_from_id(session, settings.FEDORA_REST_ENDPOINT, metadata_formats, verbosity, options["sleep"])

        for k, v in self.sets.items():
            try:
                k.sets.add(Set.objects.get(spec=v))
            except Set.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(f"Set {v} not found while adding to header {k}.")
                )

        nb_sets = Set.objects.count() - nb_sets
        nb_headers = Header.objects.count() - nb_headers

        if verbosity >= 1:
            self.stdout.write(f"Added {nb_sets} sets.")
            self.stdout.write(f"Added {nb_headers} headers.")

    def fetch_from_id(self, session, fedora_id, metadata_formats, verbosity, sleep_time):
        if verbosity >= 2:
            self.stdout.write(f"Fetch from {fedora_id}.")
        r = session.get(
            fedora_id,
            auth=settings.FEDORA_AUTH,
            headers={"Accept": "application/ld+json"},
        )

        if not r:
            return

        data = r.json()[0]
        r.close()

        if self.key_set_spec in data and self.key_set_name in data:
            if verbosity > 2:
                self.stdout.write(
                    f"Create set {data[self.key_set_name][0]['@value']}."
                )
            Set.objects.update_or_create(
                spec=data[self.key_set_spec][0]["@value"],
                name=data[self.key_set_name][0]["@value"],
            )
        else:
            if self.key_identifier in data:
                identifier = data[self.key_identifier][0]["@value"]
            else:
                identifier = f"oai:{fedora_id}"

            r_meta = session.get(fedora_id, auth=settings.FEDORA_AUTH, headers={"Accept": "application/rdf+xml"})
            try:
                root = ElementTree.fromstring(r_meta.text)
                ns = {'fedora': 'http://fedora.info/definitions/v4/repository#'}
                nodes = root.findall('.//fedora:lastModified', ns)
            except ElementTree.ParseError:
                nodes = []
            if len(nodes) < 1:
                timestamp = None
            else:
                timestamp = nodes[0].text
            if self.key_memberof in data:
                setspec = data[self.key_memberof][0]["@value"]
            else:
                setspec = None
            r_meta.close()

            if verbosity > 2:
                self.stdout.write(f"Create header {identifier}.")
            header, created = Header.objects.update_or_create(
                identifier=identifier,
                defaults={
                    "timestamp": timestamp,
                },
            )
            if setspec:
                self.sets[header] = setspec

            for k, v in settings.FEDORA_METADATA_PREDICATES.items():
                if v in data:
                    meta_binary_url = data[v][0]['@id']
                    if verbosity > 2:
                        self.stdout.write(f"Fetch from {meta_binary_url}.")
                    r_metadata = session.get(
                        meta_binary_url,
                        auth=settings.FEDORA_AUTH,
                    )
                    if r_metadata.status_code == requests.codes.ok:
                        if verbosity > 2:
                            self.stdout.write(f"Add metadata format of type {k}.")

                        XMLRecord.objects.update_or_create(
                            header=header,
                            metadata_prefix=metadata_formats[k],
                            defaults={"xml_metadata": r_metadata.text},
                        )
                        header.metadata_formats.add(metadata_formats[k])
                    r_metadata.close()

        sleep(sleep_time)
        if "http://www.w3.org/ns/ldp#contains" in data:
            for i in data["http://www.w3.org/ns/ldp#contains"]:
                self.fetch_from_id(session, i['@id'], metadata_formats, verbosity, sleep_time)
