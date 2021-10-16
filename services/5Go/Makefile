.PHONY: proto-rust
proto-rust:
	cd proto && protoc --rust_out ../synapsis/src neurotransmitter.proto

.PHONY: proto-go
proto-go:
	cd proto && \
		protoc \
			--go_out=../neuron/interop \
			--go_opt=paths=source_relative \
			--go-grpc_out=../neuron/interop \
			--go-grpc_opt=paths=source_relative \
			neurotransmitter.proto neuron.proto

.PHONY: clean
clean:
	rm -rf ./build/*

.PHONY: lib-rust
lib-rust:
	cd synapsis && cargo build --release
	mkdir -p build
	cp synapsis/target/release/libsynapsis.a build

.PHONY: test-rust
test-rust:
	cd synapsis && cargo test

.PHONY: test-go
test-go:
	cd neuron && go test ./...

.PHONY: test
test: test-go test-rust
