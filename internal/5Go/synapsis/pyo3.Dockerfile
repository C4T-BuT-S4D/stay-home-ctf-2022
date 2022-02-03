FROM rust:1.57.0-slim-bullseye

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3-dev \
        python3-pip

RUN pip install maturin cffi

WORKDIR /synapsis
COPY Cargo.toml .
COPY Cargo.lock .
RUN cargo fetch

COPY src src
RUN maturin \
        build \
        --release \
        --no-sdist \
        --strip \
        --cargo-extra-args="--features pyo3"
