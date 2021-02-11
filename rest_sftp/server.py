import logging

import flask
from flask import Blueprint

from rest_sftp import ftp_util
from rest_sftp.http_util import check_param

bp = Blueprint("sftp", __name__)

ftp = ftp_util.FtpUtil()


@bp.route("/structure", methods=["GET"])
def get_structure():
    check_param(["folder"])

    folder = flask.request.args.get("folder")
    logging.info(f"folder: {folder}")

    recursive_enabled = flask.request.args.get("recursive_enabled")
    logging.info(f"recursive_enabled: {recursive_enabled}")

    ignore_hidden_file_enabled = flask.request.args.get("ignore_hidden_file_enabled")
    logging.info(f"ignore_hidden_file_enabled: {ignore_hidden_file_enabled}")

    absolute_path_enabled = flask.request.args.get("absolute_path_enabled")
    logging.info(f"absolute_path_enabled: {absolute_path_enabled}")

    try:
        content = ftp.read_tree(folder, bool(recursive_enabled), bool(ignore_hidden_file_enabled),
                                bool(absolute_path_enabled))

        return flask.jsonify(content)
    except FileNotFoundError:
        message = f"{folder} does not exist."
        logging.error(message)
        flask.abort(flask.jsonify(message=message))


@bp.route("/", methods=["POST"])
def upload():
    check_param(["filepath"])
    check_param(["file"], request=flask.request.files)

    filepath = flask.request.values.get("filepath")
    logging.info(f"filepath: {filepath}")

    f = flask.request.files["file"]
    logging.info(f"filename: {f.filename}")

    ftp.upload(filepath, f)

    return "OK"


@bp.route("/", methods=["GET"])
def get():
    check_param(["file_paths"])

    file_paths = flask.request.args.get("file_paths")
    logging.info(f"file_paths: {file_paths}")

    zip_enabled = flask.request.args.get("zip_enabled")
    logging.info(f"zip_enabled: {zip_enabled}")

    return "OK"
