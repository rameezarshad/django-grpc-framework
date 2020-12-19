import importlib
import inspect
import os
import re

from django_grpc_bus.generics import ModelService
from django_grpc_bus.settings import message_bus_settings
from django.utils.module_loading import import_string
from grpc_health.v1 import health, health_pb2_grpc
from grpc_health.v1.health_pb2 import HealthCheckResponse
from grpc_reflection.v1alpha import reflection

SERVICER_PATTERN = re.compile(r'^add_[A-Za-z0-9]+Servicer_to_server')


class GrpcRegistry:

    def __init__(self, service, grpc_module=None):
        self._service = self.get_service(service)
        self._grpc_module = self.get_module(grpc_module or f'{self.model_name}_pb2_grpc')
        self._module = self.get_module(f'{self.model_name}_pb2')
        self._servicer = self.get_servicer()

    @staticmethod
    def get_service(service):
        if not isinstance(service, ModelService):
            service = import_string(service)
        return service

    @property
    def model_name(self):
        return self._service.queryset.model.__name__

    @staticmethod
    def get_module(module):
        producer_relative_path = os.path.relpath(message_bus_settings.PRODUCER_ROOT)
        dotted_path = producer_relative_path.replace(os.sep, '.')
        module = f'{dotted_path}.grpc.{module}'
        try:
            return importlib.import_module(module)
        except ModuleNotFoundError:
            raise ValueError(
                f'Unable to find the module {module} , '
                f'make sure to check if module exists and follow'
                f'correct syntax app_name.grpc_module'
            )

    def get_servicer(self):
        servicer = [
            func[0] for func in inspect.getmembers(self._grpc_module)
            if inspect.isfunction(func[1]) and SERVICER_PATTERN.match(func[0])
        ]
        if not servicer:
            raise ValueError(
                f'Unable to find the servicer for the module'
                f'{self._grpc_module.__name__}'
            )
        servicer = servicer[0]
        return getattr(self._grpc_module, servicer)

    def register(self, server):
        self._servicer(self._service.as_servicer(), server)

    @property
    def name(self):
        return self._module.DESCRIPTOR.services_by_name[
            f'{self.model_name}'
        ].full_name

    def __hash__(self):
        return hash((self._grpc_module.__name__, self._service.__name__))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            raise NotImplemented
        return (
                self._grpc_module.__name__ == other._grpc_module.__name__ and
                self._service.__name__ == other._service.__name__
        )


class BasicHandler:
    def __init__(self):
        self.registry = set()

    def register(self, service, grpc_module=None):
        self.registry.add(
            GrpcRegistry(grpc_module=grpc_module, service=service)
        )

    def bind_to_server(self, server, enable_reflection=True):
        service_names = [
            reflection.SERVICE_NAME,
            health.SERVICE_NAME,
        ]
        health_servicer = health.HealthServicer(experimental_non_blocking=True)
        health_servicer.set('', HealthCheckResponse.SERVING)

        for service in self.registry:
            service.register(server)
            service_names.append(service.name)
            status = HealthCheckResponse.SERVING
            health_servicer.set(service.name, status)
        health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)

        if enable_reflection:
            reflection.enable_server_reflection(service_names, server)


