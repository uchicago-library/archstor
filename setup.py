from setuptools import setup, find_packages


def readme():
    with open("README.md", 'r') as f:
        return f.read()


setup(
    name="archstor",
    description="Archstor is a web API wrapper which provides a simplified API " +
    "for several object storage backends/interfaces.",
    version="0.1.2",
    long_description=readme(),
    author="Brian Balsamo",
    author_email="brian@brianbalsamo.com",
    packages=find_packages(
        exclude=[
        ]
    ),
    include_package_data=True,
    url='https://github.com/uchicago-library/archstor',
    dependency_links=[
        'https://github.com/uchicago-library/pypairtree' +
        '/tarball/master#egg=pypairtree'
    ],
    install_requires=[
        'flask>0',
        'flask_env',
        'flask_restful',
        'pypairtree',
        'pymongo'
    ],
    tests_require=[
        'pytest'
    ],
    test_suite='tests'
)
