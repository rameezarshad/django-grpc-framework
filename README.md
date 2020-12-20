Django gRPC Framework
=====================

Django gRPC framework is an advanced toolkit for building gRPC services. It helps building the micro services and their 
communication. For instance lets consider an environment where we have multiple django projects running (or micro services), 
there will be a need of communication between them, where gRPC comes into play. This bus will be responsible for message 
transfer, so we will be having a producer and consumers.

This framework will help building the gRPC server and client that will consume the services. Building gRPC server and client 
is a complex task, so this framework will provide a basic guide to build all these components. A gRPC client requires 
***Stub*** for communicating with gRPC server (producer), which can be sometime a bit redundant to use proto files and 
Stub, for the client. So for ease of use we are using ***reflection***, that will list all the services running on a server 
with its methods. Isn't it cool? 

We only need few command to generate the ***proto*** files, update it and generates
gRPC python out files, and then focus on building services and their communication with other services.

# Requirements

* Python (3.6, 3.7, 3.8, 3.9)
* Django (2.2, 3.0, 3.1)
* Django Rest Framework (3.10, 3.11)
* grpcio (1.34x)
* grpcio-health (1.34x)
* grpcio-reflection (1.34x)
* grpcio-tools (1.34x)
* isort


Installation
------------

    $ pip install django-grpc-bus 


Add ``django_grpc_bus`` to ``INSTALLED_APPS`` setting:

    INSTALLED_APPS = [
        ...
        'django_grpc_bus',
    ]

Add ``MESSAGE_BUS`` to settings:
    
    MESSAGE_BUS = {
        'ROOT_HANDLERS_HOOK': 'path.to.handler',
        'SERVICE_META': os.path.join(BASE_DIR, 'service_meta.yaml'),
        'PRODUCER_ROOT': os.path.join(settings.BASE_DIR, 'generated_grpc'),
        'SERVICE_TEMPLATE': os.path.join(Path(__file__).resolve().parent, 'service_template'),
        'HANDLER_TEMPLATE': os.path.join(Path(__file__).resolve().parent, 'handler_template'),
        'SERVLETS': {
            'server1': {
                'host': localhost,
                'port': 50051,
            },
            'server2': {
                'host': localhost,
                'port': 50052,
            },
            'server3': {
                'host': localhost,
                'port': 50053,
            },
        }
    }

# Example

Let's take a look at a quick example of using gRPC framework to serve and consume gRPC services.

Define ``service_meta.yml`` in the project root

```yaml
apps:
  - name: app_1
    models:
      - name: model_1
        exclude:
          - exclude_field_1
          - exclude_field_2
  - name: app_2
    models:
      - name: model_2
        fields:
          - field_1
          - field_2
      - name: model_3
```
By default all apps will be used as service, or to generate default service meta yaml for all apps using:

    ./manage.py generatemetayaml --file path.to.save.file

Update the path of ``service_meta.yaml`` in MESSAGE_BUS settings.

Generate default proto files (defined in ``service_meta.yaml``) to ``PRODUCER_ROOT`` path, using:

    ./manage.py generateproto

Once the proto files are updated, generate the gRPC python out files to ``PRODUCER_ROOT`` path, using:

    ./manage.py generategrpc

Define the components ``serializers.py``, ``services.py`` and ``handlers.py``

* ``serializers.py`` are the similar to django rest serializers, example:

```python
from django_grpc_bus import serializers as proto_serializers

from path.to.generated_grpc.grpc import ModelName_pb2
from app_name import models


class ModelNameSerializer(proto_serializers.ModelProtoSerializer):

    class Meta:
        model = models.ModelName
        proto_class = ModelName_pb2.ModelNameData
```

* ``services.py`` contains the gRPC producer services, inherited from class ModelService containing predefined mixins
 ``create``, ``retrieve``, ``update``, ``destroy`` and ``list``, example to define services.py:

```python
from django_grpc_bus.generics import ModelService

from app_name import models, serializers


class ModelNameService(ModelService):
    queryset = models.ModelName.objects.all()
    serializer_class = serializers.ModelNameSerializer
```

* ``handlers.py`` are the routers for services, that register the services, example:

```python
from django_grpc_bus.handlers import BasicHandler


handler = BasicHandler()

handler.register('app_name.services.ModelNameService')

```

To start with above components simply run the following command:

    ./manage.py generateservices -hd

Predefined templates will be generated in the app directories and ``handlers.py`` will be get appended with service 
registry.

Start the server using:

    ./manage.py rungrpcserver --dev

Server will get started at 50051 port.

To consume the services, for now we are using gRPC reflection that lists all the registered services and its methods. 
Use the client as:

```python
from django_grpc_bus.client.registry import registry

list_data = registry.servlet_name.service_name.list()  # Generator object will be returned as its stream response
get_data = registry.servlet_name.service_name.retrieve({'id': 1})
```

Let's take a look on above steps in nutshell:

```shell script
./manage.py generateproto
./manage.py generategrpc
./manage.py generateservices -hd
```
* And done proto files for apps are created in PRODUCER_ROOT.
* gRPC python files are generated in PRODUCER_ROOT.
* ***serializers.py***, ***services.py*** and ***handlers.py*** are generated.

Let's start the server.

```shell script
./manage.py rungrpcserver --dev
``` 

To consume the services use the ***registry*** from ***django_grpc_bus.client.registry***.