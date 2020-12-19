from grpc._channel import _Rendezvous

from django_grpc_bus import exceptions
from django_grpc_bus.client.client import get_by_endpoint
from django_grpc_bus.settings import message_bus_settings


class Servlet:
    def __init__(self, name):
        self._name = name
        self._servlet = self._get_servlet()
        self._host = self._servlet.get('host', 'localhost')
        self._port = self._servlet.get('port', 50051)
        self._client = None

    def get_client(self):
        return get_by_endpoint(
            endpoint=f'{self._host}:{self._port}'
        )

    def check_client(self):
        if not self._client:
            try:
                self._client = self.get_client()
            except _Rendezvous as error:
                raise exceptions.GRPCException(
                    f'Unable to communicate with `{self.name}` service '
                    f'running at {self._host}:{self._port} '
                    f'due to `{error._state.details}`. Failed with '
                    f'status code `{error._state.code}`.'
                )
            for service in self._client.service_names:
                setattr(self, service, self._client.service(service))
        return self

    def _get_servlet(self):
        servers = message_bus_settings.SERVLETS
        if isinstance(servers, dict) and servers.get(self.name):
            data = servers.get(self.name)
            if isinstance(data, dict):
                return data
            raise exceptions.ServerConfigError(
                f'Invalid servlet config for {self.name}. '
                f'It must be dict object.'
            )
        raise exceptions.ServerConfigError(
            f'Unable to find the servlet config in '
            f'the settings for {self.name}. Make sure to add '
            f'correct config'
        )

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def name(self):
        return self._name

    def __getattr__(self, item):
        raise exceptions.ServiceNotFound(item, self._client.service_names)


class Registry(object):

    def __init__(self):
        self.registry_dict = self.register()

    def __getattr__(self, item) -> Servlet:
        if item in self.get_servlets():
            return self.registry_dict.get(item).check_client()
        raise exceptions.ServiceNotFound(item, self.get_servlets().keys())

    @staticmethod
    def get_servlets():
        servlets = message_bus_settings.SERVLETS
        if isinstance(servlets, dict):
            return servlets
        raise ValueError(
            f'Unable to find the servlets config in '
            f'the MESSAGE_BUS settings. Make sure to add '
            f'correct config'
        )

    def register(self):
        r_dict = dict()
        for servlet, config in self.get_servlets().items():
            r_dict.update({
                servlet: Servlet(name=servlet)
            })
        return r_dict


registry = Registry()


