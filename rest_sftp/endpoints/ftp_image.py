import logging
from http import HTTPStatus

import flask
from flask_restx import Namespace, Resource, reqparse, inputs

from rest_sftp.download import download_service
from rest_sftp.ftp import ftp_service
from rest_sftp.images.image_util import get_thumbnail_as_bytes

ftp = ftp_service.FtpService.instance()
download_service = download_service.DownloadService.instance()

api = Namespace("image")

_get_parser = reqparse.RequestParser()
_get_parser.add_argument("file_path", type=str, required=True, help="Image path to download",
                         default="/")
_get_parser.add_argument("width", type=int, required=True, help="Width to reduce the image size",
                         default=100)
_get_parser.add_argument("height", type=int, required=True, help="Height to reduce the image size",
                         default=100)


@api.route("/image")
class FTPImage(Resource):

    @api.doc("/",
             responses={
                 HTTPStatus.UNAUTHORIZED: "Request unauthorized",
                 HTTPStatus.BAD_REQUEST: "Parameters were not provided",
                 HTTPStatus.FORBIDDEN: "Request cannot be executed",
                 HTTPStatus.NOT_FOUND: "File not found",
                 HTTPStatus.OK: "File requested"
             })
    @api.produces(["image/jpeg"])
    @api.expect(_get_parser)
    def get(self):
        args = _get_parser.parse_args()

        file_path = args["file_path"]
        height = args["height"]
        width = args["width"]

        logging.info(f"args: {args}")

        try:
            path, mimetype = download_service.get_content(file_path, False)
            content = get_thumbnail_as_bytes(width, height, path)
            return flask.send_file(content, mimetype="image/jpeg")
        except FileNotFoundError as e:
            flask.abort(HTTPStatus.NOT_FOUND, description=str(e))
        except IsADirectoryError as e:
            flask.abort(HTTPStatus.FORBIDDEN, description=str(e))
