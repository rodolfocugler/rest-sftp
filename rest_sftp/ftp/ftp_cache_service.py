import logging
import os


def _find_folder_in_cache(cache, folder):
    if _is_base_path(folder):
        return cache

    directories = [item for item in cache if isinstance(item, dict)]
    for directory in directories:
        for key, value in directory.items():
            if key == folder:
                return value
            found_folder = _find_folder_in_cache(value, folder)
            if found_folder is not None:
                return found_folder

    return None


def _read_tree(cache, recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled):
    files = []
    for item in cache:
        if isinstance(item, dict):
            files_in_folder = _read_dir(item, recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled)
            if files_in_folder is not None:
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


def _read_dir(cache, recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled):
    for key, value in cache.items():
        if ignore_hidden_file_enabled and _get_filename(key).startswith("."):
            return None
        files_in_folder = _read_tree(value, recursive_enabled, ignore_hidden_file_enabled,
                                     absolute_path_enabled) \
            if recursive_enabled else []
        folder_name = key if absolute_path_enabled else _get_filename(key)
        return {folder_name: files_in_folder}


def _get_filename(absolut_path):
    return absolut_path.split(os.path.sep)[-1:][0]


def _is_base_path(local_path):
    return local_path == "fotos"


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

    def read_tree(self, local_path, recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled):
        if self.cache is None:
            return None

        logging.info("reading tree from cache")

        if _is_root_default_tree(local_path, recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled):
            return self.cache
        else:
            filtered_cache = _find_folder_in_cache(self.cache, local_path)
            if filtered_cache is None:
                raise FileNotFoundError
            return _read_tree(filtered_cache, recursive_enabled, ignore_hidden_file_enabled, absolute_path_enabled)

    def invalidate_cache(self):
        self.cache = None
