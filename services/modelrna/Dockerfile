FROM python:3.9.6-slim-bullseye

RUN apt update && apt install -y xxd
WORKDIR /app
ADD src/requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY src .

COPY config.env config.env

RUN sed -i  "s/JWT_KEY=.*/JWT_KEY=$(xxd -u -l 10 -p /dev/urandom)/g" config.env

CMD python3 main.py

