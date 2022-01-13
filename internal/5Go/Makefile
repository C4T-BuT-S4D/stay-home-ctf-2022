.PHONY: proto-rust
proto-rust:
	cd proto && \
		protoc \
			--rust_out=../synapsis/src \
			neurotransmitter.proto

.PHONY: proto-go
proto-go:
	mkdir -p neuron/interop
	cd proto && \
		protoc \
			--go_out=../neuron/interop \
			--go_opt=paths=source_relative \
			--go-grpc_out=../neuron/interop \
			--go-grpc_opt=paths=source_relative \
			neurotransmitter.proto neuron.proto

.PHONY: proto-python
proto-python:
	mkdir -p client/proto
	cd proto && \
		python -m grpc_tools.protoc \
			--proto_path=. \
			--python_out=../client/proto \
			--grpc_python_out=../client/proto \
			 neuron.proto && \
		python -m grpc_tools.protoc \
			--proto_path=. \
			--python_out=../client/proto \
			 neurotransmitter.proto

.PHONY: proto
proto: proto-go proto-rust proto-python

.PHONY: lib-rust
lib-rust:
	mkdir -p synapsis/target
	docker build \
		-t synapsis-ffi-builder \
		-f synapsis/ffi.Dockerfile \
		synapsis
	docker run \
		-it \
		-v $(shell pwd)/synapsis/target:/target \
		synapsis-builder \
		cp /synapsis/target/release/libsynapsis.a /target
	mkdir -p neuron/lib
	cp synapsis/target/libsynapsis.a neuron/lib
	cp synapsis/src/ffi.h neuron/lib

.PHONY: lib-rust-mac
lib-rust-mac:
	cd synapsis && cargo build --features ffi
	mkdir -p neuron/lib
	cp synapsis/target/debug/libsynapsis.a neuron/lib/libsynapsis.a
	cp synapsis/src/ffi.h neuron/lib

.PHONY: o3-develop
o3-develop:
	cd synapsis && \
		maturin develop \
			--cargo-extra-args="--features pyo3"

.PHONY: o3-build
o3-build:
	mkdir -p synapsis/target
	docker build \
		-t synapsis-pyo3-builder \
		-f synapsis/pyo3.Dockerfile \
		synapsis
	docker run \
		-it \
		-v $(shell pwd)/synapsis/target:/target \
		synapsis-pyo3-builder \
		cp /synapsis/target/wheels/synapsis-0.1.0-cp39-cp39-manylinux_2_24_x86_64.whl /target/synapsis-0.1.0-cp39-cp39-manylinux_2_24_x86_64.whl
	mkdir -p client/lib
	cp synapsis/target/synapsis-0.1.0-cp39-cp39-manylinux_2_24_x86_64.whl client/lib

.PHONY: test-rust
test-rust:
	cd synapsis && cargo test

.PHONY: test-go
test-go:
	cd neuron && go test ./...

.PHONY: test
test: test-go test-rust
