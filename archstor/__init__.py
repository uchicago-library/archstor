from flask import Flask
from .blueprint import BLUEPRINT
from flask_env import MetaFlaskEnv


class Configuration(metaclass=MetaFlaskEnv):
    ENV_PREFIX = 'ARCHSTOR_'
    DEBUG = False
    DEFER_CONFIG = False
    BUFF = 1024*8


app = Flask(__name__)

app.config.from_object(Configuration)

app.register_blueprint(BLUEPRINT)
