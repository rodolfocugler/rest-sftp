import io

from setuptools import find_packages
from setuptools import setup

with io.open("README.md", "rt", encoding="utf8") as f:
    readme = f.read()

setup(
    name="rest_sftp",
    version="1.0.0",
    url="https://github.com/rodolfocugler/rest-sftp",
    license="Apache 2.0",
    maintainer="Rodolfo Cugler",
    maintainer_email="rodolfocugler@outlook.com",
    description="Rest API to connect in a SFTP server",
    long_description=readme,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=["flask"],
)