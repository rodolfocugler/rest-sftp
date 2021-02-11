import os


class Config:
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", "6291456000"))

    LOGSTASH_HOST = os.getenv("LOGSTASH_HOST")
    LOGSTASH_PORT = os.getenv("LOGSTASH_PORT")
    APP_NAME = os.getenv("FLASK_APP")

    BASIC_AUTH_USERNAME = os.getenv("BASIC_AUTH_USERNAME", "admin")
    BASIC_AUTH_PASSWORD = os.getenv("BASIC_AUTH_PASSWORD", "123456")
    BASIC_AUTH_FORCE = True
