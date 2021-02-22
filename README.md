# REST-SFTP

![GitHub stars](https://img.shields.io/github/stars/rodolfocugler/rest-sftp?logo=github) ![Docker Stars](https://img.shields.io/docker/stars/rodolfocugler/rest-sftp?label=stars&logo=docker) ![Docker Pulls](https://img.shields.io/docker/pulls/rodolfocugler/rest-sftp?label=pulls&logo=docker)

![logo](https://raw.githubusercontent.com/rodolfocugler/rest-sftp/main/logo.png)

# Supported tags and respective `Dockerfile` links

- [`x86` (*Dockerfile*)](https://github.com/rodolfocugler/rest-sftp/blob/main/Dockerfile) ![Docker Image Size (x86)](https://img.shields.io/docker/image-size/rodolfocugler/rest-sftp/x86?label=python&logo=python&style=plastic)
- [`arm64v8` (*Dockerfile*)](https://github.com/rodolfocugler/rest-sftp/blob/arm64v8/Dockerfile) ![Docker Image Size (arm64v8)](https://img.shields.io/docker/image-size/rodolfocugler/rest-sftp/arm64v8?label=arm64v8&logo=raspberry%20pi&style=plastic)

obs.: in order to run the container in an arm32v7 platform you can build the arm32v7 branch [(*Dockerfile*)](https://github.com/rodolfocugler/rest-sftp/blob/arm32v7/Dockerfile)

# Securely share your files

Easy REST API to access your SFTP ([SSH File Transfer Protocol](https://en.wikipedia.org/wiki/SSH_File_Transfer_Protocol)) Server

# Usage

Rest-SFTP allows you to access your SFTP server through a rest API. Have a look on [rodolfocugler/sftp](https://hub.docker.com/r/rodolfocugler/sftp) if you don't have SFTP server.

### Environment variables

Following are the available environment variables:

- APP_NAME: application name
- BASIC_AUTH_USERNAME: username to authenticate on application
- BASIC_AUTH_PASSWORD: password to authenticate on application
- SFTP_HOSTNAME: hostname or IP of your SFTP server
- SFTP_PORT: port of your SFTP server (usually 22)
- SFTP_USERNAME: username to authenticate on the SFTP server
- SFTP_KEY_PATH: path of the key file to authenticate on the SFTP server (should be mounted as volume)
- SFTP_BASE_FOLDER: base folder of your SFTP server (it may be /home/username/Desktop)
- LOGSTASH_HOST (optional): hostname or IP of your logstash server
- LOGSTASH_PORT (optional): port of your logstash server

### Documentation

The postman collection can be found [here](https://github.com/rodolfocugler/rest-sftp/blob/main/collections).

Also, accessing your application url http://rest-sftp:80/ you will find the Swagger Documentation.

# Examples

## Simple docker run example

Let's assume that you have a SFTP up and running:

```
cp path/to/sftp/key key
docker run \
    -e APP_NAME=rest-sftp \
    -e BASIC_AUTH_USERNAME=admin \
    -e BASIC_AUTH_PASSWORD=password \
    -e SFTP_HOSTNAME=sftp \
    -e SFTP_USERNAME=admin \
    -e SFTP_KEY_PATH=/usr/src/app/key \
    -e SFTP_PORT=22 \
    -e SFTP_BASE_FOLDER=root \
    -v $(pwd)/key:/usr/src/app/key \
    -p 80:80 \
    --name rest-sftp \
    -d rodolfocugler/rest-sftp:x86
```

### Using Docker Compose:
```
---
version: "3.8"

services:
  rest-sftp:
    image: rodolfocugler/rest-sftp:x86
    restart: always
    volumes:
      - ./key:/usr/src/app/key:ro
    ports:
      - "80:80"
    environment:
      APP_NAME: rest-sftp
      BASIC_AUTH_USERNAME: admin
      BASIC_AUTH_PASSWORD: password
      SFTP_HOSTNAME: sftp
      SFTP_USERNAME: admin
      SFTP_KEY_PATH: /usr/src/app/key
      SFTP_PORT: 22
      SFTP_BASE_FOLDER: root
```

### Launching SFTP + Rest-SFTP:

```
git clone https://github.com/rodolfocugler/rest-sftp.git
cd rest-sftp/example
docker-compose up -d
```
