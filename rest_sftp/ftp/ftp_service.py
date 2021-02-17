import logging
import os
import stat

from rest_sftp.ftp.ftp_cache_service import FtpCacheService
from rest_sftp.ftp.ftp_connection import FTPConnection
from rest_sftp.ftp.ftp_connection_pool import FTPConnectionPool
from rest_sftp.singleton import Singleton

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


def _is_dir(conn, filepath):
    return stat.S_ISDIR(conn.stat(filepath).st_mode)


def _filepath_exists(conn, filepath):
    try:
        conn.stat(filepath)
        return True
    except FileNotFoundError:
        return False


def _rename_old_filepath(conn, old_remote_path, is_dir):
    attempt = 1
    new_remote_path = None
    while attempt == 1 or _filepath_exists(conn, new_remote_path):
        if is_dir:
            new_remote_path = f"{old_remote_path[:-1]}_{attempt}/"
        else:
            path = os.path.splitext(old_remote_path)
            new_remote_path = f"{path[0]}_{attempt}{path[1]}"
        attempt += 1

    conn.posix_rename(old_remote_path, new_remote_path)


def _delete_dir(conn, remote_path):
    files = conn.listdir(remote_path)

    for f in files:
        filepath = os.path.join(remote_path, f)
        if _is_dir(conn, filepath):
            _delete_dir(conn, filepath)
        else:
            conn.remove(filepath)

    conn.rmdir(remote_path)


@Singleton
class FtpService:

    def __init__(self):
        self.pool = FTPConnectionPool(sftp_hostname=SFTP_HOSTNAME, sftp_username=SFTP_USERNAME,
                                      sftp_key_path=SFTP_KEY_PATH, sftp_port=SFTP_PORT,
                                      factory=FTPConnection.open_connection, capacity=SFTP_CONNECTION_POOL_CAPACITY)
        self.cacheService = FtpCacheService()

    def read_tree(self, folder, recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled):
        remote_path, local_path = _get_remote_and_local_path(folder)

        content = self.cacheService.read_tree(folder, local_path, recursive_enabled, ignore_hidden_file_enabled,
                                              absolute_path_enabled)
        if content is not None:
            return content

        conn = self.pool.get_resource().sftp
        logging.info("reading tree")
        content = _read_tree(recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled, conn, remote_path,
                             local_path)

        self.cacheService.save_cache(content, local_path, recursive_enabled, ignore_hidden_file_enabled,
                                     absolute_path_enabled)

        return content

    def get_file(self, filepath, rest_local_path):
        remote_path, _ = _get_remote_and_local_path(filepath)
        conn = self.pool.get_resource().sftp
        logging.info(f"downloading {remote_path} to {rest_local_path}")
        conn.get(remote_path, rest_local_path)
        logging.info(f"downloaded {remote_path} to {rest_local_path}")

    def upload(self, filepath, f, filename=None):
        remote_path, _ = _get_remote_and_local_path(filepath)
        conn = self.pool.get_resource().sftp
        _create_dir(conn, remote_path)

        if isinstance(f, str):
            remote_path = os.path.join(remote_path, filename)
            logging.info(f"uploading {remote_path} to {f}")
            conn.put(f, remote_path)
            logging.info(f"uploaded {remote_path} to {f}")
        else:
            remote_path = os.path.join(remote_path, f.filename)
            logging.info(f"uploading file to {remote_path}")
            conn.putfo(f, remote_path)
            logging.info(f"file uploaded to {remote_path}")
        self.cacheService.invalidate_cache()

    def delete(self, filepath):
        remote_path, _ = _get_remote_and_local_path(filepath)
        conn = self.pool.get_resource().sftp

        if _is_dir(conn, remote_path):
            _delete_dir(conn, remote_path)
        else:
            conn.remove(remote_path)
        self.cacheService.invalidate_cache()

    def move_to_bin(self, filepath):
        remote_path, _ = _get_remote_and_local_path(filepath)
        conn = self.pool.get_resource().sftp

        new_remote_path, _ = _get_remote_and_local_path(os.path.join(".trash", filepath))
        old_remote_path, _ = _get_remote_and_local_path(filepath)

        is_dir = _is_dir(conn, old_remote_path)
        if _filepath_exists(conn, new_remote_path):
            _rename_old_filepath(conn, new_remote_path, is_dir)

        _create_dir(conn, new_remote_path, is_dir)
        conn.posix_rename(old_remote_path, new_remote_path)
        self.cacheService.invalidate_cache()

    def filepath_exists(self, filepath):
        conn = self.pool.get_resource().sftp
        remote_path, _ = _get_remote_and_local_path(filepath)
        return _filepath_exists(conn, remote_path)

    def is_filepath_a_dir(self, filepath):
        conn = self.pool.get_resource().sftp
        remote_path, _ = _get_remote_and_local_path(filepath)
        return stat.S_ISDIR(conn.stat(remote_path).st_mode)
