import logging

from flask_restx import Namespace, Resource, reqparse, inputs
from werkzeug.datastructures import FileStorage

from rest_sftp.ftp import ftp_service

ftp = ftp_service.FtpService.instance()

api = Namespace("ftp")

_post_parser = reqparse.RequestParser()
_post_parser.add_argument("filepath", type=str, required=True, help="Folder where the file will be saved")
_post_parser.add_argument("f", type=FileStorage, location="files", help="File", required=True)

_get_parser = reqparse.RequestParser()
_get_parser.add_argument("file_paths", type=str, required=True, help="File paths to download joined by `;`", default="/")
_get_parser.add_argument("zip_enabled", type=inputs.boolean, required=False, help="Zip all files before downloading", default=True)


@api.route("/ftp")
class FTPFile(Resource):

    @api.doc("/",
             responses={
                 401: "UNAUTHORIZED",
                 200: "OK",
                 400: "BAD REQUEST"
             })
    @api.expect(_post_parser)
    def post(self):
        args = _post_parser.parse_args()

        filepath = args["filepath"]
        f = args["f"]

        logging.info(f"args: {args}")

        ftp.upload(filepath, f)

        return "OK"

    @api.doc("/",
             responses={
                 401: "UNAUTHORIZED",
                 200: "OK",
                 400: "BAD REQUEST"
             })
    @api.expect(_get_parser)
    def get(self):
        args = _get_parser.parse_args()

        file_paths = args["file_paths"]
        zip_enabled = args["zip_enabled"]

        logging.info(f"args: {args}")

        return "OK"
