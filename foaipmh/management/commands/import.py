"""Fedora OAI-PMH Django app import command."""

import requests

from django.conf import settings
from django.core.management.base import BaseCommand
from oai_pmh.models import DCRecord, Header, MetadataFormat, Set, XMLRecord
from time import sleep


class Command(BaseCommand):
    """Fedora OAI-PMH import command."""

    help = "Import metadata from Fedora."

    key_set_spec = "http://www.openarchives.org/OAI/2.0setSpec"
    key_set_name = "http://www.openarchives.org/OAI/2.0setName"
    key_identifier = "http://purl.org/dc/elements/1.1/identifier"
    key_created = "http://fedora.info/definitions/v4/repository#created"
    key_memberof = "http://purl.org/dc/elements/1.1/memberOf"

    def add_arguments(self, parser):
        """Add arguments."""
        parser.add_argument(
            "-s",
            "--sleep",
            type=int,
            default=5,
            help="Sleep intervall in sec. To prevent to many requests in short time. "
            + "Default: 5",
        )

    def handle(self, *args, **options):
        """Handle command."""
        verbosity = int(options["verbosity"])

        metadata_formats = {}
        for k, v in settings.FEDORA_METADATA_SUFFIX.items():
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

        r = requests.get(
            settings.FEDORA_REST_ENDPOINT,
            auth=settings.FEDORA_AUTH,
            headers={"Accept": "application/ld+json"},
        )

        nb_sets = Set.objects.count()
        nb_headers = Header.objects.count()

        sets = {}
        for i in r.json()[0]["http://www.w3.org/ns/ldp#contains"]:
            if verbosity >= 2:
                self.stdout.write(f"Fetch from {i['@id']}.")
            r = requests.get(
                i["@id"],
                auth=settings.FEDORA_AUTH,
                headers={"Accept": "application/ld+json"},
            )

            data = r.json()[0]

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
                    identifier = f"oai:{i['@id']}"
                if "self.key_created" in data:
                    timestamp = data["self.key_created"][0]["@value"]
                else:
                    timestamp = None
                if self.key_memberof in data:
                    setspec = data[self.key_memberof][0]["@value"]
                else:
                    setspec = None

                if verbosity > 2:
                    self.stdout.write(f"Create header {identifier}.")
                header, created = Header.objects.update_or_create(
                    identifier=identifier,
                    defaults={
                        "timestamp": timestamp,
                    },
                )
                if setspec:
                    sets[header] = setspec

                for k, v in settings.FEDORA_METADATA_SUFFIX.items():
                    if verbosity > 2:
                        self.stdout.write(f"Fetch from {i['@id']}{v}.")
                    r = requests.get(
                        f'{i["@id"]}{v}',
                        auth=settings.FEDORA_AUTH,
                    )
                    if r.status_code == requests.codes.ok:
                        if verbosity > 2:
                            self.stdout.write(f"Add metadata format of type {k}.")
                        if k == "oai_dc":
                            dcrecord, created = DCRecord.from_xml(r.text, header)
                            if dcrecord:
                                header.metadata_formats.add(
                                    MetadataFormat.objects.get(prefix="oai_dc")
                                )
                        else:
                            XMLRecord.objects.update_or_create(
                                header=header,
                                metadata_prefix=metadata_formats[k],
                                defaults={"xml_metadata": r.text},
                            )
                            header.metadata_formats.add(metadata_formats[k])

            sleep(options["sleep"])

        for k, v in sets:
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
