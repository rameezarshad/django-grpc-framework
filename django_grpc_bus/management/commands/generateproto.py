import os

from django_grpc_bus.protobuf.generators import ModelProtoGenerator
from django_grpc_bus.utils import service_meta
from django_grpc_bus.utils.generators import ProtoGenerator
from django.core.management.base import BaseCommand, CommandError
from django.utils.module_loading import import_string


class Command(BaseCommand):
    help = "Generates proto."

    def add_arguments(self, parser):
        parser.add_argument(
            '--model', dest='model', type=str, default=None,
            help='dotted path to a model class',
        )
        parser.add_argument(
            '--fields', dest='fields', default=None, type=str,
            help='specify which fields to include, comma-separated'
        )
        parser.add_argument(
            '--file', dest='file', default=None, type=str,
            help='the generated proto file path'
        )
        parser.add_argument(
            '--config', dest='config', default=None, type=str,
            help='File containing apps and models config'
        )

    def legacy_generator(self, **options):
        model = import_string(options['model'])
        fields = list(map(str.strip, options['fields'].split(','))) if options['fields'] else None
        filepath = options['file']
        if filepath and os.path.exists(filepath):
            raise CommandError('File "%s" already exists.' % filepath)
        if filepath:
            package = os.path.splitext(os.path.basename(filepath))[0]
        else:
            package = None
        generator = ModelProtoGenerator(
            model=model,
            field_names=fields,
            package=package,
        )
        proto = generator.get_proto()
        if filepath:
            with open(filepath, 'w') as f:
                f.write(proto)
        else:
            self.stdout.write(proto)

    def handle(self, *args, **options):
        if options['model']:
            self.legacy_generator(**options)
        else:
            file = options['config']
            meta = None
            if file:
                if not os.path.lexists(file):
                    raise CommandError(f'Config file {file} does not exists.')
                meta = service_meta.ServiceMeta(file)
            ProtoGenerator(meta=meta).generate_producer()


