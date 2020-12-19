
from typing import List


class GRPCException(Exception):
    pass


class RegisterError(GRPCException):
    pass


class ServerConfigError(GRPCException):
    pass


class ServerSSLConfigError(ServerConfigError):
    pass


class ProtobufError(GRPCException):
    pass


class ServiceNotFound(ProtobufError):
    def __init__(self, service_name, available_services=None, **kwargs):
        self.fail_service = service_name
        self.services = available_services

    def __str__(self):
        msg = f"Unable to find `{self.fail_service}` service."
        return f"{msg} Available services are `{', '.join(self.services)}`" if self.services else msg


class MethodNotFound(ProtobufError):
    def __init__(self, method_name, service_name=None, available_methods: List[str] = None, **kwargs):
        self.fail_method = method_name
        self.service_name = service_name or ''
        self.methods = available_methods

    def __str__(self):
        msg = f"Can not find {self.fail_method} in {self.service_name}."
        return f"{msg} available methods is {', '.join(self.methods)}" if self.methods else msg
