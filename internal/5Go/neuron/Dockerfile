FROM golang:1.17.5-bullseye as builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc

WORKDIR /neuron
COPY go.mod .
COPY go.sum .
RUN go mod download

COPY . .
RUN CGO_ENABLED=1 go build -o neuron ./cmd/neuron/main.go

FROM debian:bullseye
COPY --from=builder /neuron/neuron /neuron
CMD ["/neuron"]
