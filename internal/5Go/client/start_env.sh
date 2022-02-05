#!/bin/bash -e

cat <<EOF >Dockerfile
FROM python:3.9
COPY . .
RUN pip install -r requirements.txt && \
    pip install lib/synapsis-0.1.0-cp39-cp39-manylinux_2_24_x86_64.whl

ENTRYPOINT ["python", "client.py"]
EOF

docker build -t 5go_env .
docker run -it 5go_env $@

