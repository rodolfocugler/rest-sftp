import logging
import os

from flask import Flask
from flask_basicauth import BasicAuth
from logstash_async.formatter import LogstashFormatter
from logstash_async.handler import AsynchronousLogstashHandler

from rest_sftp.endpoints import api


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY=os.urandom(16))

    from rest_sftp import config
    app.config.from_object(config.Config())

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from rest_sftp.endpoints import ftp_file

    api.init_app(app)
    configure_logging(app)
    BasicAuth(app)
    return app


def configure_logging(app):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    stdout_handler = logging.StreamHandler()
    formatter = logging.Formatter(fmt='%(asctime)s %(pathname)s:%(lineno)d - %(levelname)s - %(message)s',
                                  datefmt='%d-%b-%y %H:%M:%S')
    stdout_handler.setFormatter(formatter)
    logger.addHandler(stdout_handler)

    if app.config["LOGSTASH_HOST"] is not None:
        logstash_handler = AsynchronousLogstashHandler(
            app.config["LOGSTASH_HOST"],
            int(app.config["LOGSTASH_PORT"]),
            database_path=None
        )
        logstash_handler.setFormatter(
            LogstashFormatter(
                message_type="python-logstash",
                extra=dict(
                    application=app.config["APP_NAME"],
                    environment=app.config["ENV"]
                )
            )
        )
        logger.addHandler(logstash_handler)
