import glob
import logging
import os
import shutil
import subprocess

from django_grpc_bus.protobuf import generators
from django_grpc_bus.settings import message_bus_settings
from django_grpc_bus.utils import service_meta

logger = logging.getLogger(__name__)


class ProtoGenerator:
    RETRY_COUNT = 0

    def __init__(self, meta=None):
        self._meta = service_meta.get_meta(meta)

    @staticmethod
    def get_or_create_path(path):
        # Get or create the path
        os.makedirs(path, exist_ok=True)
        return path

    @classmethod
    def save_proto(cls, model_name, proto, path):
        logger.info(f'Saving Proto file to {path}..')
        path = os.path.join(
            cls.get_or_create_path(path),
            f'{model_name}.proto'
        )
        with open(path, 'w') as f:
            f.write(proto)

    @classmethod
    def generate_proto(cls, app_name, model, path):
        generator = generators.ModelProtoGenerator(
            model=model.model,
            field_names=model.fields,
            package=f'{app_name}'
        )
        proto = generator.get_proto()
        cls.save_proto(
            model.model.__name__,
            proto,
            os.path.join(path, 'proto')
        )

    def generate_producer(self, apps=None):
        logger.info('Generating Proto files for producer..')
        if apps is None:
            apps = self._meta.apps
        for app in apps:
            for model in app.models:
                self.generate_proto(
                    app.app.name,
                    model,
                    message_bus_settings.PRODUCER_ROOT
                )

    def check_proto_files(self, path, apps=None):
        logger.info('Checking Proto files..')
        if apps and isinstance(apps, (list, tuple)):
            rebuild_apps = []
            for app in apps:
                for model in app.models:
                    if len(glob.glob(os.path.join(path, '**', f'{model.name}.proto'))) == 0:
                        rebuild_apps.append(app)
            self.generate_producer(apps=rebuild_apps)
        elif len(glob.glob(os.path.join(path, '**', '*.*'))) == 0:
            logger.info('Proto files does not exists, regenerating files.')
            self.generate_producer()

    def generate_grpc(self, apps=None):
        producer_root = message_bus_settings.PRODUCER_ROOT
        logger.info('Generating the GRPC files..')
        root_path = os.path.dirname(producer_root)
        producer_name = os.path.basename(producer_root)
        self.check_proto_files(producer_root, apps)
        grpc_path = self.get_or_create_path(os.path.join(producer_root, 'grpc'))
        self.copy_temp_proto(os.path.join(producer_root, '**'), grpc_path)
        try:
            subprocess.check_output(
                f'python -m grpc_tools.protoc --proto_path={root_path}/ '
                f'--python_out=. --grpc_python_out=. {producer_name}/grpc/*.proto',
                stderr=subprocess.STDOUT, shell=True
            )
        except Exception as e:
            print(e)
            logger.error(e)
        self.delete_temp_proto(grpc_path)

    @staticmethod
    def copy_temp_proto(from_path, dest_dir):
        for file in glob.glob(os.path.join(from_path, '*.proto')):
            if os.path.isfile(file):
                shutil.copy2(file, dest_dir)

    @staticmethod
    def delete_temp_proto(path):
        for file in glob.glob(os.path.join(path, '*.proto')):
            os.remove(file)

