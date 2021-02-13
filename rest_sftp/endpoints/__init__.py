from flask_restx import Api

from rest_sftp.endpoints.ftp_file import api as ns_ftp_file
from rest_sftp.endpoints.ftp_structure import api as ns_ftp_structure

api = Api(
    title='Rest-SFTP',
    version='1.0',
    description='Connect to a SFTP server through a Rest API'
)

api.add_namespace(ns_ftp_file, path="/api")
api.add_namespace(ns_ftp_structure, path="/api")
