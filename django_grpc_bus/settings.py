"""
Settings for messagebus are all namespaced in the MESSAGE_BUS setting.
For example your project's `settings.py` file might look like this:

MESSAGE_BUS = {
    'ROOT_HANDLERS_HOOK': 'path.to.handler',
    'SERVICE_META': os.path.join(BASE_DIR, 'service_meta.yaml'),
    'PRODUCER_ROOT': os.path.join(settings.BASE_DIR, 'generated_grpc'),
    'SERVICE_TEMPLATE': os.path.join(Path(__file__).resolve().parent, 'service_template'),
    'HANDLER_TEMPLATE': os.path.join(Path(__file__).resolve().parent, 'handler_template'),
    'SERVLETS': {
        'service1': {
            'host': localhost,
            'port': 50051,
        },
        'service2': {
            'host': localhost,
            'port': 50052,
        },
        'service3': {
            'host': localhost,
            'port': 50053,
        },
    }
}

This module provides the `message_bus_settings` object, that is used to access
message bus settings, checking for user settings first, then falling
back to the defaults.
"""
import os

from django.conf import settings
from django.test.signals import setting_changed
from django.utils.module_loading import import_string
from pathlib import Path

DEFAULTS = {
    'ROOT_HANDLERS_HOOK': None,
    'SERVER_INTERCEPTORS': None,
    'SERVICE_META': None,
    'PRODUCER_ROOT': os.path.join(settings.BASE_DIR, 'generated_grpc'),
    'SERVICE_TEMPLATE': os.path.join(Path(__file__).resolve().parent, 'service_template'),
    'HANDLER_TEMPLATE': os.path.join(Path(__file__).resolve().parent, 'handler_template'),
    'SERVICE_TIMEOUT': 15,
    'SERVLETS': {}
}


# List of settings that may be in string import notation.
IMPORT_STRINGS = [
    'ROOT_HANDLERS_HOOK',
    'SERVER_INTERCEPTORS',
    'SERVICE_META',
    'PRODUCER_ROOT',
    'SERVICE_TEMPLATE',
    'HANDLER_TEMPLATE',
    'SERVICE_TIMEOUT',
    'SERVLETS',
]


def perform_import(val, setting_name):
    """
    If the given setting is a string import notation,
    then perform the necessary import or imports.
    """
    if val is None:
        return None
    elif isinstance(val, str) and os.sep not in val:
        return import_from_string(val, setting_name)
    elif isinstance(val, (list, tuple)):
        return [import_from_string(item, setting_name) for item in val]
    return val


def import_from_string(val, setting_name):
    """
    Attempt to import a class from a string representation.
    """
    try:
        return import_string(val)
    except ImportError as e:
        raise ImportError(
            "Could not import '%s' for message bus setting '%s'. %s: %s." %
            (val, setting_name, e.__class__.__name__, e)
        )


class MessageBusSettings:
    """
    A settings object that allows message bus settings to be accessed as
    properties. For example:

        from message_bus.settings import message_bus_settings
        print(message_bus_settings.ROOT_HANDLERS_HOOK)

    Any setting with string import paths will be automatically resolved
    and return the class, rather than the string literal.
    """
    def __init__(self, user_settings=None, defaults=None, import_strings=None):
        if user_settings:
            self._user_settings = user_settings
        self.defaults = defaults or DEFAULTS
        self.import_strings = import_strings or IMPORT_STRINGS
        self._cached_attrs = set()

    @property
    def user_settings(self):
        if not hasattr(self, '_user_settings'):
            self._user_settings = getattr(settings, 'MESSAGE_BUS', {})
        return self._user_settings

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError("Invalid message bus setting: '%s'" % attr)

        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        # Coerce import strings into classes
        if attr in self.import_strings:
            val = perform_import(val, attr)

        # Cache the result
        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def reload(self):
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, '_user_settings'):
            delattr(self, '_user_settings')


message_bus_settings = MessageBusSettings(None, DEFAULTS, IMPORT_STRINGS)


def reload_mb_settings(*args, **kwargs):
    setting = kwargs['setting']
    if setting == 'MESSAGE_BUS':
        message_bus_settings.reload()


setting_changed.connect(reload_mb_settings)
