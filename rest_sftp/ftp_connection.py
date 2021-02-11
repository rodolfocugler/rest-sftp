import logging

import paramiko


class FTPConnection:

    def __init__(self, ssh, sftp):
        self.ssh = ssh
        self.sftp = sftp

    def __getitem__(self, item):
        return item

    @staticmethod
    def open_connection(sftp_hostname, sftp_username, sftp_key_path, sftp_port):
        logging.info("opening sftp connection")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(sftp_hostname, username=sftp_username, key_filename=sftp_key_path, port=sftp_port)
        max_transfer_size = 2 ** 30
        ssh.get_transport().window_size = max_transfer_size
        ssh.get_transport().max_packet_size = max_transfer_size
        return FTPConnection(ssh, ssh.open_sftp())
