FROM python:3.9.6-alpine

ADD requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

ADD src /app

WORKDIR /app

CMD ["flask", "run", "--host", "0.0.0.0"]
