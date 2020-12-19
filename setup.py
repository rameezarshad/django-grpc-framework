from setuptools import find_packages, setup

setup(
    name='django_grpc_bus',
    version=1.0,
    description='Django rest gRPC framework',
    url='https://github.com/rameezarshad/django-grpc-framework',
    download_url='https://github.com/rameezarshad/django-grpc-framework/archive/main.zip',
    author='Rameez Arshad',
    author_email='rameez.arshad@outlook.in',
    packages=find_packages(),
    install_requires=[
        "django>=2.2",
        "djangorestframework>=3.10",
        "grpcio>=1.34.0",
        "grpcio-health-checking>=1.34.0",
        "grpcio-reflection>=1.34.0",
        "grpcio-tools>=1.34.0",
        "isort>=5.6.4",
    ],
    python_requires=">=3.6",
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Framework',
        'License :: OSI Approved :: GNU General Public License License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='grpc framework django rest micro service message bus',

)
