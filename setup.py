from setuptools import setup, find_packages

def readme():
    with open("README.md", 'r') as f:
        return f.read()

setup(
    name = "archstor",
    description = "abstract layer for archival object storage",
    long_description = readme(),
    packages = find_packages(
        exclude = [
        ]
    ),
    dependency_links = [
        'https://github.com/bnbalsamo/pypairtree' +
        '/tarball/master#egg=pypairtree'
    ],
    install_requires = [
        'flask>0',
        'flask_env',
        'flask_restful',
        'pypairtree',
        'pymongo'
    ],
)
