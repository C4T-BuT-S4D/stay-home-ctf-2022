FROM ubuntu:20.04

RUN apt-get update && apt-get upgrade -yyq
RUN apt-get install socat -yyq

ADD --chown=root ./kuar-server /kuar-server

WORKDIR /

CMD ["socat", "TCP-LISTEN:1337,reuseaddr,fork,keepalive", "EXEC:./kuar-server"]
