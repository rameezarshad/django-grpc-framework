from setuptools import find_packages, setup

setup(
    name='django-grpc-bus',
    version='1.0.2',
    description='Django rest gRPC framework',
    long_description=open('README.md', 'r', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
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
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='grpc framework django rest micro service message bus',

)
