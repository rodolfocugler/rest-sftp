import logging
import os


def _read_tree(cache, recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled,
               local_path):
    files = []
    for item in cache:
        if isinstance(item, dict):
            files_in_folder = _read_dir(item, recursive_enabled, ignore_hidden_file_enabled,
                                        absolute_path_enabled, local_path)

            if isinstance(files_in_folder, list):
                return files_in_folder

            files.append(files_in_folder)
        else:
            f = _read_file(item, ignore_hidden_file_enabled, absolute_path_enabled)
            if f is not None:
                files.append(f)
    return files


def _read_file(cache, ignore_hidden_file_enabled, absolute_path_enabled):
    filename = _get_filename(cache)
    if not ignore_hidden_file_enabled or not filename.startswith("."):
        return cache if absolute_path_enabled else filename
    return None


def _read_dir(cache, recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled, local_path):
    for key, value in cache.items():
        files_in_folder = _read_tree(value, recursive_enabled, ignore_hidden_file_enabled,
                                     absolute_path_enabled, local_path) \
            if not _is_base_path(local_path) or recursive_enabled else []
        folder_name = key if absolute_path_enabled else _get_filename(key)
        return {folder_name: files_in_folder} if local_path != key else files_in_folder


def _get_filename(absolut_path):
    return absolut_path.split(os.path.sep)[-1:][0]


def _is_base_path(local_path):
    return local_path == "/"


def _is_root_default_tree(local_path, recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled):
    return _is_base_path(local_path) \
           and recursive_enabled \
           and not ignore_hidden_file_enabled \
           and absolute_path_enabled


class FtpCacheService:

    def __init__(self):
        self.cache = None

    def save_cache(self, content, local_path, recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled):
        if _is_root_default_tree(local_path, recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled):
            logging.info("saving cache")
            self.cache = content

    def delete_cache(self):
        logging.info("deleting cache")
        self.cache = None

    def read_tree(self, folder, local_path, recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled):
        if self.cache is None:
            return None

        logging.info("reading tree from cache")

        if _is_root_default_tree(local_path, recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled):
            return self.cache
        else:
            return _read_tree(self.cache, recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled,
                              folder)
