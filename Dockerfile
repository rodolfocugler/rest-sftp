FROM arm32v7/python:3.9

RUN apt update && apt upgrade -y
RUN apt install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    cargo \
    curl
 
RUN curl -o rust-init.sh --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs && \
    sh rust-init.sh -y && \
    rm rust-init.sh

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY ./ .

CMD ["waitress-serve", "--port=80", "--call",  "rest_sftp:create_app"]
