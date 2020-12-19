# -*- coding: utf-8 -*-
import errno
import os
import re
import sys
from datetime import datetime

from django_grpc_bus.server import Server
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import autoreload
from django.utils.regex_helper import _lazy_re_compile

naiveip_re = _lazy_re_compile(r"""^(?:
(?P<ipv6>\[[a-fA-F0-9:]+\])
:)?(?P<port>\d+)$""", re.X)


class Command(BaseCommand):
    help = 'Starts a gRPC server.'

    # Validation is called explicitly each time the server is reloaded.
    requires_system_checks = False
    default_addr = '[::]'
    default_port = '50051'

    def add_arguments(self, parser):
        parser.add_argument(
            'address', nargs='?',
            help='Optional address for which to open a port.'
        )
        parser.add_argument(
            '--max-workers', type=int, default=10, dest='max_workers',
            help='Number of maximum worker threads.'
        )
        parser.add_argument(
            '--dev', action='store_true', dest='development_mode',
            help=(
                'Run the server in development mode.  This tells Django to use '
                'the auto-reloader and run checks.'
            )
        )

    def handle(self, *args, **options):
        if not options['address']:
            self.address, self.port = self.default_addr, self.default_port
        else:
            m = re.match(naiveip_re, options['address'])
            if m is None:
                raise CommandError(
                    '"%s" is not a valid port number or address:port pair.' % options['address']
                )
            self.address, self.port = m.groups()
        self.run(**options)

    def run(self, **options):
        """Run the server, using the autoreloader if needed."""
        if options['development_mode']:
            if hasattr(autoreload, "run_with_reloader"):
                autoreload.run_with_reloader(self.inner_run, **options)
            else:
                autoreload.main(self.inner_run, None, options)
        else:
            self.stdout.write(f"Starting gRPC server at {self.address}:{self.port}\n")
            Server(
                host=self.address,
                port=self.port,
                worker=options['max_workers']
            ).run()

    def inner_run(self, *args, **options):
        # If an exception was silenced in ManagementUtility.execute in order
        # to be raised in the child process, raise it now.
        autoreload.raise_last_exception()

        self.stdout.write("Performing system checks...\n\n")
        self.check(display_num_errors=True)
        # Need to check migrations here, so can't use the
        # requires_migrations_check attribute.
        self.check_migrations()
        now = datetime.now().strftime('%B %d, %Y - %X')
        self.stdout.write(now)
        quit_command = 'CTRL-BREAK' if sys.platform == 'win32' else 'CONTROL-C'
        self.stdout.write((
            "Django version %(version)s, using settings %(settings)r\n"
            "Starting development gRPC server at %(address)s\n"
            "Quit the server with %(quit_command)s.\n"
        ) % {
            "version": self.get_version(),
            "settings": settings.SETTINGS_MODULE,
            "address": options['max_workers'],
            "quit_command": quit_command,
        })
        try:
            Server(
                host=self.address,
                port=self.port,
                worker=options['max_workers']
            ).run()
        except OSError as e:
            # Use helpful error messages instead of ugly tracebacks.
            ERRORS = {
                errno.EACCES: "You don't have permission to access that port.",
                errno.EADDRINUSE: "That port is already in use.",
                errno.EADDRNOTAVAIL: "That IP address can't be assigned to.",
            }
            try:
                error_text = ERRORS[e.errno]
            except KeyError:
                error_text = e
            self.stderr.write("Error: %s" % error_text)
            # Need to use an OS exit because sys.exit doesn't work in a thread
            os._exit(1)
        except KeyboardInterrupt:
            sys.exit(0)
