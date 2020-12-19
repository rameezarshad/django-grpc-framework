import os

import yaml
from django_grpc_bus.utils import service_meta
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Generates Service Meta YAML."

    def add_arguments(self, parser):
        parser.add_argument('apps', nargs='?', help='Name of the applications.')
        parser.add_argument(
            '--file', dest='file', default=None, type=str,
            help='File containing apps and models config'
        )

    def handle(self, *args, **options):
        apps = options['apps']
        file = options['file']
        meta_dict = {'apps': []}
        if apps:
            apps = list(map(str.strip, apps.split(',')))
            for app in apps:
                meta_dict['apps'].append({
                    'name': app
                })
        meta_object = service_meta.ServiceMeta(meta_dict)
        meta_yaml = yaml.safe_dump(meta_object.as_serializer())
        if file:
            if not os.path.lexists(file):
                raise CommandError(f'Config file {file} does not exists.')
            with open(file, 'w') as f:
                f.write(meta_yaml)
        else:
            self.stdout.write(meta_yaml)





