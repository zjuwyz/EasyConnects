from setuptools import setup, find_packages

setup(
    name='easyconnects',
    version='0.1',
    description='A socket server utility module',
    packages=find_packages(),  # This will find all your packages automatically
    install_requires=[
        'zmq',  # This is the only dependency
    ]
)
