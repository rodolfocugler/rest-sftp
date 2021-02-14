import logging
from http import HTTPStatus

from flask_restx import Namespace, Resource, reqparse

from rest_sftp.download import download_service

download_service = download_service.DownloadService.instance()

api = Namespace("url")

_post_parser = reqparse.RequestParser()
_post_parser.add_argument("filename", type=str, required=True, help="Name to save the file")
_post_parser.add_argument("filepath", type=str, required=True, help="Folder where the file will be saved")
_post_parser.add_argument("url", type=str, required=True, help="URL to download the file")


@api.route("/url")
class FTPImage(Resource):

    @api.doc("/",
             responses={
                 HTTPStatus.UNAUTHORIZED: "Request unauthorized",
                 HTTPStatus.BAD_REQUEST: "Parameters were not provided",
                 HTTPStatus.OK: "File was uploaded successfully"
             })
    @api.expect(_post_parser)
    def post(self):
        args = _post_parser.parse_args()

        filename = args["filename"]
        filepath = args["filepath"]
        url = args["url"]

        logging.info(f"args: {args}")

        download_service.upload_from_download(filepath, filename, url)
