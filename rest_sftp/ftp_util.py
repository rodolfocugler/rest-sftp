import logging
import os
import stat

from rest_sftp.ftp_connection import FTPConnection
from rest_sftp.ftp_connection_pool import FTPConnectionPool

SFTP_HOSTNAME = os.getenv("SFTP_HOSTNAME")
SFTP_USERNAME = os.getenv("SFTP_USERNAME")
SFTP_KEY_PATH = os.getenv("SFTP_KEY_PATH")
SFTP_PORT = int(os.getenv("SFTP_PORT", "22"))
SFTP_BASE_FOLDER = os.getenv("SFTP_BASE_FOLDER")
SFTP_CONNECTION_POOL_CAPACITY = int(os.getenv("SFTP_CONNECTION_POOL_CAPACITY", "20"))


def _get_remote_and_local_path(folder):
    if folder != "/" and folder != "":
        return os.path.join(SFTP_BASE_FOLDER, folder), folder
    else:
        return SFTP_BASE_FOLDER, "/"


def _read_tree(recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled, conn, remote_path, local_path):
    files = []
    for f in conn.listdir_attr(remote_path):
        path = _get_file_path(absolute_path_enabled, local_path, f)
        if stat.S_ISDIR(f.st_mode):
            files_in_folder = _read_tree(recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled, conn,
                                         os.path.join(remote_path, f.filename), path) \
                if recursive_enabled \
                else []
            files.append({path: files_in_folder})
        elif not ignore_hidden_file_enabled or not f.filename.startswith("."):
            files.append(path)

    return files


def _get_file_path(full_path_enabled, local_path, f):
    return os.path.join(local_path, f.filename) if full_path_enabled else f.filename


def _is_base_path(local_path):
    return local_path == "/"


def _is_root_default_tree(local_path, recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled):
    return _is_base_path(local_path) \
           and recursive_enabled \
           and not ignore_hidden_file_enabled \
           and absolute_path_enabled


def _tree_from_cache(cache, recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled,
                     local_path):
    files = []
    for item in cache:
        if isinstance(item, dict):
            files_in_folder = _read_dir_from_cache(item, recursive_enabled, ignore_hidden_file_enabled,
                                                   absolute_path_enabled, local_path)

            if isinstance(files_in_folder, list):
                return files_in_folder

            files.append(files_in_folder)
        else:
            f = _read_file_from_cache(item, ignore_hidden_file_enabled, absolute_path_enabled)
            if f is not None:
                files.append(f)
    return files


def _read_file_from_cache(cache, ignore_hidden_file_enabled, absolute_path_enabled):
    filename = _get_filename(cache)
    if not ignore_hidden_file_enabled or not filename.startswith("."):
        return cache if absolute_path_enabled else filename
    return None


def _read_dir_from_cache(cache, recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled, local_path):
    for key, value in cache.items():
        files_in_folder = _tree_from_cache(value, recursive_enabled, ignore_hidden_file_enabled,
                                           absolute_path_enabled, local_path) \
            if not _is_base_path(local_path) or recursive_enabled else []
        folder_name = key if absolute_path_enabled else _get_filename(key)
        return {folder_name: files_in_folder} if local_path != key else files_in_folder


def _get_filename(absolut_path):
    return absolut_path.split(os.path.sep)[-1:][0]


def _create_dir(conn, remote_path, is_dir=True):
    dirs = remote_path.split(os.path.sep)
    current_dir = dirs[0]
    last_index = len(dirs) if is_dir else len(dirs) - 1
    for d in dirs[1:last_index]:
        current_dir = os.path.join(current_dir, d)
        try:
            if not stat.S_ISDIR(conn.stat(current_dir).st_mode):
                conn.mkdir(current_dir)
        except FileNotFoundError:
            conn.mkdir(current_dir)


class FtpUtil:

    def __init__(self):
        self.pool = FTPConnectionPool(sftp_hostname=SFTP_HOSTNAME, sftp_username=SFTP_USERNAME,
                                      sftp_key_path=SFTP_KEY_PATH, sftp_port=SFTP_PORT,
                                      factory=FTPConnection.open_connection, capacity=SFTP_CONNECTION_POOL_CAPACITY)
        self.cache = None

    def read_tree(self, folder, recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled):
        if self.cache is not None:
            return self._tree_from_cache(folder, recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled)

        conn = self.pool.get_resource().sftp
        remote_path, local_path = _get_remote_and_local_path(folder)
        logging.info("reading tree")
        content = _read_tree(recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled, conn, remote_path,
                             local_path)

        if _is_root_default_tree(local_path, recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled):
            self.cache = content

        return content

    def _tree_from_cache(self, folder, recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled):
        remote_path, local_path = _get_remote_and_local_path(folder)
        if _is_root_default_tree(local_path, recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled):
            return self.cache
        else:
            return _tree_from_cache(self.cache, recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled,
                                    folder)

    def get_file(self, filepath, local_path):
        remote_filepath = os.path.join(SFTP_BASE_FOLDER, filepath)
        conn = self.pool.get_resource().sftp
        logging.info(f"downloading {remote_filepath} to {local_path}")
        conn.get(remote_filepath, local_path)
        logging.info(f"downloaded {remote_filepath} to {local_path}")

    def upload(self, filepath, f):
        remote_filepath = os.path.join(SFTP_BASE_FOLDER, filepath)
        conn = self.pool.get_resource().sftp
        _create_dir(conn, remote_filepath)

        if isinstance(f, str):
            remote_filepath = os.path.join(remote_filepath, os.path.basename(f))
            logging.info(f"uploading {remote_filepath} to {f}")
            conn.put(f, remote_filepath)
            logging.info(f"uploaded {remote_filepath} to {f}")
        else:
            remote_filepath = os.path.join(remote_filepath, f.filename)
            logging.info(f"uploading file to {remote_filepath}")
            conn.putfo(f, remote_filepath)
            logging.info(f"file uploaded to {remote_filepath}")
