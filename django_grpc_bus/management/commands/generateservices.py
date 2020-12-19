import os
import sys

import isort
from django_grpc_bus.settings import message_bus_settings
from django_grpc_bus.utils import service_meta
from django.core.management.base import BaseCommand, CommandError
from django.template import Engine, Context

import settings


class Command(BaseCommand):
    help = "Generates GRPC services."
    rewrite_template_suffixes = (
        # Allow shipping invalid .py files without byte-compilation.
        ('.py-tpl', '.py'),
    )

    def add_arguments(self, parser):
        parser.add_argument('name', nargs='?', help='Name of the application.')
        parser.add_argument(
            '--handler', '-hd', action='store_true', dest='save_handler',
            default=False, help='Option to save the handler template'
        )
        parser.add_argument(
            '--config', dest='file', default=None, type=str,
            help='File containing apps and models config'
        )
        parser.add_argument(
            '--edit', '-e', dest='edit', default=False, action='store_true',
            help='Edit the files instead of overwriting.'
        )
        parser.add_argument(
            '--force', '-f', dest='force', default=False, action='store_true',
            help='Force overwrite all the files.'
        )

    def query_yes_no(self, question, default="no"):
        """Ask a yes/no question via raw_input() and return their answer.

        "question" is a string that is presented to the user.
        "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

        The "answer" return value is True for "yes" or False for "no".
        """
        valid = {"yes": True, "y": True, "ye": True,
                 "no": False, "n": False}
        if default is None:
            prompt = " [y/n] "
        elif default == "yes":
            prompt = " [Y/n] "
        elif default == "no":
            prompt = " [y/N] "
        else:
            raise ValueError("invalid default answer: '%s'" % default)

        while True:
            choice = input(question + prompt).lower()
            if default is not None and choice == '':
                return valid[default]
            elif choice in valid:
                return valid[choice]
            else:
                sys.stdout.write("Please respond with 'yes' or 'no' (or 'y' or 'n').\n")

    def generate_service(self, app, edit=False, force=False):
        producer_relative_path = os.path.relpath(message_bus_settings.PRODUCER_ROOT)
        dotted_path = producer_relative_path.replace(os.sep, '.')
        context = Context({
            'app_name': app.app.name,
            'models': app.models,
            'producer': dotted_path,
        })
        app_path = os.path.join(settings.BASE_DIR, app.app.name)

        for root, dirs, files in os.walk(message_bus_settings.SERVICE_TEMPLATE):

            for filename in files:
                old_path = os.path.join(root, filename)
                new_path = os.path.join(app_path, filename)
                for old_suffix, new_suffix in self.rewrite_template_suffixes:
                    if new_path.endswith(old_suffix):
                        new_path = new_path[:-len(old_suffix)] + new_suffix
                        break  # Only rewrite once
                if os.path.exists(new_path) and not (edit or force):
                    if not self.query_yes_no(
                            self.style.ERROR(f'{new_path} already exists in {app.app.name}. \n') +
                            self.style.WARNING(f'Do you want to overwrite the file or skip it?')
                    ):
                        sys.stdout.write(
                            self.style.SUCCESS(
                                f'\nSkipping {new_path} from overwriting.\n\n\n'
                            )
                        )
                        continue

                with open(old_path, encoding='utf-8') as template_file:
                    content = template_file.read()
                template = Engine().from_string(content)
                content = template.render(context)
                content = isort.code(content)
                mode = 'a' if edit else 'w'
                with open(new_path, mode, encoding='utf-8') as new_file:
                    new_file.write(content)

    def generate_handler(self, apps):
        _apps = []
        for app in apps:
            for model in app.models:
                _apps.append(
                    (app.name, model.name)
                )
        context = Context({
            'write_headers': True,
            'apps': _apps,
        })

        for root, dirs, files in os.walk(message_bus_settings.HANDLER_TEMPLATE):

            for filename in files:
                old_path = os.path.join(root, filename)
                new_path = os.path.join(settings.BASE_DIR, filename)
                for old_suffix, new_suffix in self.rewrite_template_suffixes:
                    if new_path.endswith(old_suffix):
                        new_path = new_path[:-len(old_suffix)] + new_suffix
                        break  # Only rewrite once
                with open(old_path, encoding='utf-8') as template_file:
                    content = template_file.read()
                template = Engine().from_string(content)

                mode = 'w'
                if os.path.exists(new_path):
                    context.update({
                        'write_headers': False
                    })
                    mode = 'a'

                content = template.render(context)
                with open(new_path, mode, encoding='utf-8') as new_file:
                    new_file.write(content)

    def handle(self, *args, **options):
        names = options['name']
        file = options['file']
        edit = options['edit']
        force = options['force']
        save_handler = options['save_handler']
        apps = service_meta.get_meta().apps
        if file:
            if not os.path.lexists(file):
                raise CommandError(f'Config file {file} does not exists.')
            apps = service_meta.ServiceMeta(file).apps

        if names:
            names = list(map(str.strip, names.split(',')))
            apps = list(filter(lambda x: x.app.name in names, apps))

        for app in apps:
            self.generate_service(app, edit, force)
        if save_handler:
            self.generate_handler(apps)

