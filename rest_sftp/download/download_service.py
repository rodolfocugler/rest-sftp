import logging
import mimetypes
import os
import queue
import shutil
import uuid
import zipfile
from datetime import datetime
from urllib.request import urlretrieve

import rest_sftp
from rest_sftp.ftp import ftp_service
from rest_sftp.singleton import Singleton


def _get_mimetype(filename):
    return mimetypes.guess_type(filename)[0] or "application/octet-stream"


def _get_base_folder():
    folder = os.path.join(os.path.dirname(rest_sftp.__file__), "tmp", "files")
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder


def _zip_files(downloaded_files, reference_files):
    logging.info(f"zipping files")
    identifier = str(uuid.uuid4())
    local_path = os.path.join(_get_base_folder(), f"{identifier}.zip")
    with zipfile.ZipFile(local_path, "w", zipfile.ZIP_DEFLATED, True, 9) as zf:
        for i in range(len(downloaded_files)):
            f = downloaded_files[i]
            f_ref = reference_files[i]
            zf.write(f, os.path.basename(f_ref))
    [os.remove(f) for f in downloaded_files]
    return local_path


@Singleton
class DownloadService:

    def __init__(self):
        self.ftp = ftp_service.FtpService.instance()
        self.files_to_delete = queue.Queue()

    def get_content(self, file_paths, zip_enabled):
        file_paths = file_paths.split(";")
        file_paths = list(filter(lambda path: '' != path, file_paths))
        self._check_if_files_exist(file_paths)
        downloaded_files = self._download_files(file_paths)
        filepath = _zip_files(downloaded_files, file_paths) \
            if zip_enabled or len(downloaded_files) > 1 \
            else downloaded_files[0]
        logging.info(f"sending files")
        return filepath, _get_mimetype(filepath)

    def _download_files(self, file_paths):
        downloaded_files = []
        base_folder = _get_base_folder()
        for filepath in file_paths:
            logging.info(f"filepath: {filepath}")
            filename = os.path.basename(filepath)
            identifier = str(uuid.uuid4())
            local_path = os.path.join(base_folder, f"{identifier}{filename}")
            self.ftp.get_file(filepath, local_path)
            downloaded_files.append(local_path)
            self.add_file_to_queue(local_path)
        return downloaded_files

    def _check_if_files_exist(self, file_paths):
        not_found_files = []
        found_folders = []
        for filepath in file_paths:
            if not self.ftp.filepath_exists(filepath):
                not_found_files.append(filepath)

            if self.ftp.is_filepath_a_dir(filepath):
                found_folders.append(filepath)

        if len(not_found_files) > 0:
            message = f"{not_found_files} not found."
            logging.error(message)
            raise FileNotFoundError(message)

        if len(found_folders) > 0:
            message = f"Folder cannot be downloaded ({found_folders})."
            logging.error(message)
            raise IsADirectoryError(message)

    def upload_from_download(self, filepath, filename, url):
        identifier = str(uuid.uuid4())
        local_path = os.path.join(_get_base_folder(), f"{identifier}{filename}")
        urlretrieve(url, local_path)
        self.ftp.upload(filepath, local_path, filename)
        os.remove(local_path)

    def add_file_to_queue(self, path):
        self.files_to_delete.put({
            "size": os.stat(path).st_size,
            "timestamp": datetime.now(),
            "path": path
        })

    def delete_files(self):
        logging.info("deleting files")
        size = self.files_to_delete.qsize()
        date = datetime.now()
        for i in range(size):
            f = self.files_to_delete.get()
            delta_in_seconds = (date - f["timestamp"]).total_seconds()
            size_in_mb = f["size"] / 1000000
            if size_in_mb / delta_in_seconds <= 1:
                logging.info(f"deleting {f['path']}")
                os.remove(f["path"])
            else:
                self.files_to_delete.put(f)

    @staticmethod
    def recreate_base_folder():
        logging.info("recreating base folder")
        folder = _get_base_folder()
        if os.path.exists(folder):
            shutil.rmtree(folder)
        os.makedirs(folder)
