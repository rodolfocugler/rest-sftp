from cuttlepool import CuttlePool


class FTPConnectionPool(CuttlePool):

    def normalize_resource(self, resource):
        return resource

    def ping(self, resource):
        return resource is not None \
               and resource.ssh is not None \
               and resource.ssh.get_transport() is not None \
               and resource.ssh.get_transport().is_active()
