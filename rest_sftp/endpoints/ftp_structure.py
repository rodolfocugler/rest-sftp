import logging
from http import HTTPStatus

import flask
from flask_restx import Namespace, Resource, reqparse, inputs

from rest_sftp.ftp import ftp_service

ftp = ftp_service.FtpService.instance()

api = Namespace("tree")

_get_parser = reqparse.RequestParser()
_get_parser.add_argument("folder", type=str, required=True, help="Folder to read the tree", default="/")
_get_parser.add_argument("recursive_enabled", type=inputs.boolean, required=False,
                         help="Read tree in deep starting from folder", default=True)
_get_parser.add_argument("ignore_hidden_file_enabled", type=inputs.boolean, required=False,
                         help="Ignore files starting by `.`", default=False)
_get_parser.add_argument("absolute_path_enabled", type=inputs.boolean, required=False,
                         help="Appending the full path to the files", default=True)


@api.route("/tree")
class FTPTree(Resource):

    @api.doc("/",
             responses={
                 HTTPStatus.UNAUTHORIZED: "Request unauthorized",
                 HTTPStatus.BAD_REQUEST: "Parameters were not provided",
                 HTTPStatus.NOT_FOUND: "Folder not found",
                 HTTPStatus.OK: "Folder structure requested"
             })
    @api.expect(_get_parser)
    def get(self):
        args = _get_parser.parse_args()

        folder = args["folder"]
        recursive_enabled = args["recursive_enabled"]
        ignore_hidden_file_enabled = args["ignore_hidden_file_enabled"]
        absolute_path_enabled = args["absolute_path_enabled"]

        logging.info(f"args: {args}")

        try:
            content = ftp.read_tree(folder, recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled)

            return flask.jsonify(content)
        except FileNotFoundError:
            message = f"{folder} does not exist."
            logging.error(message)
            flask.abort(HTTPStatus.NOT_FOUND, description=message)
