import json
import os

import yaml
from django_grpc_bus.settings import message_bus_settings
from django import apps


class BaseSerializable:
    attrs = ()

    @property
    def to_json(self):
        return json.dumps(self.as_serializer())

    def as_serializer(self):
        result = {}
        for k in self.attrs:
            v = getattr(self, k)
            if isinstance(v, BaseSerializable):
                result[k] = v.as_serializer()
            elif isinstance(v, list):
                result[k] = []
                for val in v:
                    if isinstance(val, BaseSerializable):
                        result[k].append(val.as_serializer())
                    else:
                        result[k].append(val)
            else:
                result[k] = v
        return self._filter_none(result)

    @staticmethod
    def _filter_none(obj):
        """Filters out attributes set to None prior to serialization, and
        returns a new object without those attributes. This saves
        the serializer from sending empty bytes over the network. This method also
        fixes the keys to look as expected by ignoring a leading '_' if it
        is present.
        """
        result = {}
        for k, v in obj.items():
            if v is not None:
                if k.startswith('_'):
                    k = k[1:]
                result[k] = v
        return result


class Model(BaseSerializable):
    attrs = ('name', 'fields')

    def __init__(self, name, **kwargs):
        self._app_name = kwargs.pop('app_name', None)
        self._name = name
        self._model = self.get_model(self._app_name, name)
        self._all_fields = [field.name for field in self._model._meta.fields]
        self._fields = self.get_fields(**kwargs)

    @staticmethod
    def get_model(app_name, model_name):
        if isinstance(model_name, str):
            if not app_name:
                raise ValueError('Make sure to have correct app name')
            model_name = apps.apps.get_model(app_name, model_name)
        return model_name

    def get_fields(self, fields=None, exclude=None):
        field_list = []
        if fields and exclude:
            raise ValueError(
                f'Error in configuration of {self._app_name}.{self._name}, '
                '`fields` and `exclude` can not be used together.'
            )
        elif not (fields or exclude):
            fields = self.all_fields
        if fields and isinstance(fields, (tuple, list)):
            for field in fields:
                if self.model._meta.get_field(field):
                    field_list.append(field)
        elif exclude and isinstance(exclude, (tuple, list)):
            for field in self.all_fields:
                if field not in exclude:
                    field_list.append(field)
        return field_list

    @property
    def model(self):
        return self._model

    @property
    def fields(self):
        return self._fields

    @property
    def name(self):
        return self._model.__name__

    @property
    def all_fields(self):
        return self._all_fields


class App(BaseSerializable):
    attrs = ('name', 'models')

    def __init__(self, name, models=None):
        self._name = name
        self._app = self.get_app(name)
        self._models = self.get_models(models)

    @staticmethod
    def get_app(name):
        if isinstance(name, str):
            name = apps.apps.get_app_config(name)
        return name

    def get_models(self, models):
        _models = []
        if not models:
            for model in self._app.get_models():
                _models.append(Model(model))
        elif isinstance(models, (tuple, list)):
            for model in models:
                if isinstance(model, dict):
                    _models.append(Model(app_name=self.name, **model))
        return _models

    @property
    def app(self):
        return self._app

    @property
    def models(self):
        return self._models

    @property
    def name(self):
        return self._app.name


class ServiceMeta(BaseSerializable):
    attrs = ('apps',)

    def __init__(self, _meta):
        self._service_meta = self.read_meta(_meta)
        self._apps = self.get_apps(self._service_meta.get('apps'))

    @staticmethod
    def read_meta(content):
        if isinstance(content, dict):
            return content
        elif isinstance(content, str):
            content = open(content, 'r').read()
            try:
                return yaml.safe_load(content)
            except:
                return json.loads(content)
        else:
            raise ValueError(
                f'Unable to read the service meta content {content}'
            )

    def get_apps(self, app_meta):
        _apps = []
        if not app_meta:
            for app in apps.apps.get_app_configs():
                _apps.append(App(app))
        elif isinstance(app_meta, (tuple, list)):
            for app in app_meta:
                if isinstance(app, dict):
                    _apps.append(App(**app))
        return _apps

    @property
    def apps(self):
        return self._apps

    @property
    def meta(self):
        return self._service_meta


def get_meta(meta=None):
    meta = meta or message_bus_settings.SERVICE_META
    if not os.path.lexists(meta):
        raise ValueError(
            f'Service Meta {meta} file does not exists.'
        )
    return ServiceMeta(meta)




