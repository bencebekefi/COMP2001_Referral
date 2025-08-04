import os
import pathlib

basedir = pathlib.Path(__file__).parent.resolve()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_default_secret_key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SWAGGER_URL = '/api/docs'
    API_URL     = '/swagger.json'

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URI',
        "mssql+pyodbc://BBekefi:AqrM335*@DIST-6-505.uopnet.plymouth.ac.uk/COMP2001_BBekefi"
        "?driver=FreeTDS"
        "&TDS_Version=8.0"
        "&host_is_server=yes"
    )

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'TEST_DATABASE_URI',
        'sqlite:///:memory:'
    )

class ProductionConfig(Config):
    DEBUG   = False
    TESTING = False
