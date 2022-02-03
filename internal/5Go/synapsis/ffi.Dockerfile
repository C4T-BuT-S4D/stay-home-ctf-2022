FROM rust:1.57.0-slim-bullseye

WORKDIR /synapsis
COPY Cargo.toml .
COPY Cargo.lock .
RUN cargo fetch

COPY src src
RUN cargo build \
        --release \
        --features ffi
