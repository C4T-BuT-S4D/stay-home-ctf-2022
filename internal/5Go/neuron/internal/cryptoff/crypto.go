package cryptoff

/*
#cgo LDFLAGS: ./lib/libsynapsis.a -ldl -lm
#include "../../lib/ffi.h"
*/
import "C"
import (
	"errors"
	"fmt"
	"unsafe"

	"google.golang.org/protobuf/proto"

	npb "neuron/interop"
)

var (
	ErrInBuffer = errors.New("buffer has error")
)

func GenerateKey() ([]byte, error) {
	return unpackBuffer(C.generate_key_ffi())
}

func GenerateShared(pair []byte, pk []byte) ([]byte, error) {
	pairBuf := packBuffer(pair)
	pkBuf, err := serializeForRust(pk)
	if err != nil {
		return nil, fmt.Errorf("serializing pk: %w", err)
	}
	return unpackBuffer(C.generate_shared_ffi(pairBuf, pkBuf))
}

func Encrypt(key []byte, message []byte) ([]byte, error) {
	keyBuf := packBuffer(key)
	msgBuf, err := serializeForRust(message)
	if err != nil {
		return nil, fmt.Errorf("serializing message: %w", err)
	}
	return unpackBuffer(C.encrypt_ffi(keyBuf, msgBuf))
}

func Decrypt(key []byte, encrypted []byte) ([]byte, error) {
	keyBuf := packBuffer(key)
	encBuf := packBuffer(encrypted)
	return deserializeFromRust(C.decrypt_ffi(keyBuf, encBuf))
}

func packBuffer(buf []byte) C.struct_Buffer {
	res := C.struct_Buffer{}
	res.len = C.ulong(len(buf))
	res.data = (*C.char)(unsafe.Pointer(&buf[0]))
	res.error = 0
	return res
}

func unpackBuffer(buf C.struct_Buffer) ([]byte, error) {
	defer C.free_buf(buf)
	if buf.error != 0 {
		return nil, ErrInBuffer
	}
	dataPtr := unsafe.Pointer(buf.data)
	data := C.GoBytes(dataPtr, C.int(buf.len))
	result := make([]byte, len(data))
	copy(result, data)
	return result, nil
}

func serializeForRust(buf []byte) (C.struct_Buffer, error) {
	data, err := proto.Marshal(&npb.SerializedStuff{Content: buf})
	if err != nil {
		return C.struct_Buffer{}, fmt.Errorf("marshalling stuff: %w", err)
	}
	return packBuffer(data), nil
}

func deserializeFromRust(buf C.struct_Buffer) ([]byte, error) {
	raw, err := unpackBuffer(buf)
	if err != nil {
		return nil, fmt.Errorf("unpacking buffer: %w", err)
	}
	var dec npb.SerializedStuff
	if err := proto.Unmarshal(raw, &dec); err != nil {
		return nil, fmt.Errorf("deserializing stuff: %w", err)
	}
	return dec.Content, nil
}
