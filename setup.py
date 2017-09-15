from setuptools import setup, find_packages


def readme():
    with open("README.md", 'r') as f:
        return f.read()


setup(
    name="archstor",
    description="Archstor is a web API wrapper which provides a simplified API for several object storage backends/interfaces.",
    version="0.0.1",
    long_description=readme(),
    author="Brian Balsamo",
    author_email="brian@brianbalsamo.com",
    packages=find_packages(
        exclude=[
        ]
    ),
    include_package_data=True,
    url='https://github.com/bnbalsamo/archstor',
    install_requires=[
        'flask>0',
        'flask_env',
        'flask_restful'
    ],
    tests_require=[
        'pytest'
    ],
    test_suite='tests'
)
