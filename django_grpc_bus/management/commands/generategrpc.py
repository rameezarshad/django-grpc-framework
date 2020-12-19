import os

from django_grpc_bus.utils import generators, service_meta
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Generates GRPC."

    def add_arguments(self, parser):
        parser.add_argument('name', nargs='?', help='Name of the application.')
        parser.add_argument(
            '--config', dest='file', default=None, type=str,
            help='File containing apps and models config'
        )

    def handle(self, *args, **options):
        names = options['name']
        file = options['file']
        meta = None
        apps = service_meta.get_meta().apps

        if file:
            if not os.path.lexists(file):
                raise CommandError(f'Config file {file} does not exists.')
            apps = service_meta.ServiceMeta(file).apps
        if names:
            names = list(map(str.strip, names.split(',')))
            apps = list(filter(lambda x: x.app.name in names, apps))
        generators.ProtoGenerator(meta=meta).generate_grpc(apps=apps)


