import logging

import flask


def check_param(params, request=None):
    if request is None:
        request = flask.request.values

    for param in params:
        if param not in request:
            message = f"Parameter {param} is expected."
            logging.error(message)
            flask.abort(flask.jsonify(message=message))
