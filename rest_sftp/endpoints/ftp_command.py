import logging
from http import HTTPStatus

import flask
from flask_restx import Namespace, Resource, reqparse, inputs
from werkzeug.datastructures import FileStorage

from rest_sftp.download import download_service
from rest_sftp.ftp import ftp_service

ftp = ftp_service.FtpService.instance()
download_service = download_service.DownloadService.instance()

api = Namespace("commands")

_post_parser = reqparse.RequestParser()
_post_parser.add_argument("filepath", type=str, required=True, help="Folder where the file will be saved",
                          default="/")
_post_parser.add_argument("f", type=FileStorage, location="files", help="File", required=True)

_put_parser = reqparse.RequestParser()
_put_parser.add_argument("filepath_from", type=str, required=True, help="Filepath where the file is saved",
                         default="/")
_put_parser.add_argument("filepath_to", type=str, required=True, help="Filepath where the file will be saved",
                         default="/")

_get_parser = reqparse.RequestParser()
_get_parser.add_argument("file_paths", type=str, required=True, help="File paths to download joined by `;`",
                         default="/")
_get_parser.add_argument("zip_enabled", type=inputs.boolean, required=False, help="Zip all files before downloading",
                         default=True)

_delete_parser = reqparse.RequestParser()
_delete_parser.add_argument("filepath", type=str, required=True, help="Filepath to delete (folder or file)",
                            default="/")
_delete_parser.add_argument("move_to_bin_enabled", type=inputs.boolean, required=False, default=True,
                            help="Move file or folder to the bin (`.trash`) instead of delete it")


@api.route("/commands")
class FTPCommand(Resource):

    @api.doc("/",
             responses={
                 HTTPStatus.UNAUTHORIZED: "Request unauthorized",
                 HTTPStatus.BAD_REQUEST: "Parameters were not provided",
                 HTTPStatus.FORBIDDEN: "Request cannot be executed",
                 HTTPStatus.OK: "Filepath was updated successfully"
             })
    @api.expect(_put_parser)
    def put(self):
        try:
            args = _put_parser.parse_args()

            filepath_from = args["filepath_from"]
            filepath_to = args["filepath_to"]

            logging.info(f"args: {args}")

            ftp.move(filepath_from, filepath_to)
        except FileNotFoundError:
            message = f"{filepath_from} or {filepath_to} does not exist."
            logging.error(message)
            flask.abort(HTTPStatus.NOT_FOUND, description=message)
        except (PermissionError, OSError):
            message = "Request cannot be executed"
            logging.error(message)
            flask.abort(HTTPStatus.FORBIDDEN, description=message)

    @api.doc("/",
             responses={
                 HTTPStatus.UNAUTHORIZED: "Request unauthorized",
                 HTTPStatus.BAD_REQUEST: "Parameters were not provided",
                 HTTPStatus.FORBIDDEN: "Request cannot be executed",
                 HTTPStatus.OK: "File was uploaded successfully"
             })
    @api.expect(_post_parser)
    def post(self):
        try:
            args = _post_parser.parse_args()

            filepath = args["filepath"]
            f = args["f"]

            logging.info(f"args: {args}")

            ftp.upload(filepath, f)
        except PermissionError:
            message = "Request cannot be executed"
            logging.error(message)
            flask.abort(HTTPStatus.FORBIDDEN, description=message)

    @api.doc("/",
             responses={
                 HTTPStatus.UNAUTHORIZED: "Request unauthorized",
                 HTTPStatus.BAD_REQUEST: "Parameters were not provided",
                 HTTPStatus.FORBIDDEN: "Request cannot be executed",
                 HTTPStatus.NOT_FOUND: "File not found",
                 HTTPStatus.OK: "File requested"
             })
    @api.produces(["application/zip", "application/octet-stream"])
    @api.expect(_get_parser)
    def get(self):
        args = _get_parser.parse_args()

        file_paths = args["file_paths"]
        zip_enabled = args["zip_enabled"]

        logging.info(f"args: {args}")

        try:
            path, mimetype = download_service.get_content(file_paths, zip_enabled)

            return flask.send_file(path, mimetype=mimetype)
        except FileNotFoundError as e:
            flask.abort(HTTPStatus.NOT_FOUND, description=str(e))
        except IsADirectoryError as e:
            flask.abort(HTTPStatus.FORBIDDEN, description=str(e))
        except PermissionError:
            message = "Request cannot be executed"
            logging.error(message)
            flask.abort(HTTPStatus.FORBIDDEN, description=message)

    @api.doc("/",
             responses={
                 HTTPStatus.UNAUTHORIZED: "Request unauthorized",
                 HTTPStatus.BAD_REQUEST: "Parameters were not provided",
                 HTTPStatus.NOT_FOUND: "File not found",
                 HTTPStatus.FORBIDDEN: "Request cannot be executed",
                 HTTPStatus.OK: "File delete successfully"
             })
    @api.expect(_delete_parser)
    def delete(self):
        args = _delete_parser.parse_args()

        filepath = args["filepath"]
        move_to_bin_enabled = args["move_to_bin_enabled"]

        try:
            if move_to_bin_enabled:
                ftp.move_to_bin(filepath)
            else:
                ftp.delete(filepath)
        except FileNotFoundError:
            message = f"{filepath} does not exist."
            logging.error(message)
            flask.abort(HTTPStatus.NOT_FOUND, description=message)
        except PermissionError:
            message = "Request cannot be executed"
            logging.error(message)
            flask.abort(HTTPStatus.FORBIDDEN, description=message)
