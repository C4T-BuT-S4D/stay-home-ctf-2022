FROM ubuntu:20.04

RUN apt-get update && apt-get upgrade -yyq
RUN apt-get install socat -yyq

ADD --chown=root ./kuar-server /kuar-server
ADD --chown=root ./runner.sh /runner.sh
RUN chmod ugo+x ./kuar-server

WORKDIR /

CMD "./runner.sh"