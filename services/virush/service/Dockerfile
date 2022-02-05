FROM ubuntu:20.04

RUN apt update && \
    apt install -y openssl xxd

RUN useradd -s /bin/false virush

ADD bin/shx bin/websocketd /usr/bin/

RUN chmod +x /usr/bin/shx /usr/bin/websocketd

RUN mkdir -p /tmp/keys_directory \
    && chmod 777 /tmp/keys_directory

RUN mkdir -p /tmp/storage_directory \
    && chmod 777 /tmp/storage_directory

ADD run.sh /var/

RUN chmod +x /var/run.sh

ADD src /var/virush

USER virush

ENTRYPOINT ["/var/run.sh"]
