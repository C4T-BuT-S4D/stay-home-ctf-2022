package service

import (
	"context"
	"fmt"

	"go.uber.org/zap"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/types/known/emptypb"

	"neuron/internal/cryptoff"
	npb "neuron/interop"
)

func NewNeuronService() *NeuronService {
	return &NeuronService{}
}

type NeuronService struct {
	npb.UnimplementedNeuronAPIServer
}

func (s *NeuronService) Ping(context.Context, *emptypb.Empty) (*emptypb.Empty, error) {
	return &emptypb.Empty{}, nil
}

func (s *NeuronService) Session(server npb.NeuronAPI_SessionServer) error {
	im, err := server.Recv()
	if err != nil {
		return logErrorf(codes.InvalidArgument, "reading initial message: %v", err)
	}

	sessSecret, err := cryptoff.GenerateKey()
	if err != nil {
		return logErrorf(codes.Internal, "generating session private key: %v", err)
	}
	sessShared, err := cryptoff.GenerateShared(sessSecret, im.GetContent())
	if err != nil {
		return logErrorf(codes.InvalidArgument, "generating session secret: %v", err)
	}
	var parsedSecret npb.AsymmetricKey
	if err := proto.Unmarshal(sessSecret, &parsedSecret); err != nil {
		return logErrorf(codes.Internal, "unmarshalling session secret: %v", err)
	}
	if err := server.Send(parsedSecret.GetPublicKey()); err != nil {
		return logErrorf(codes.Internal, "sending public key: %v", err)
	}
	// Handshake finished

	// some helpers
	decryptReq := func(stuff *npb.SerializedStuff) ([]byte, error) {
		data, err := cryptoff.Decrypt(sessShared, stuff.GetContent())
		if err != nil {
			return nil, fmt.Errorf("decrypting message: %w", err)
		}
		return data, nil
	}
	encryptResp := func(data []byte) (*npb.SerializedStuff, error) {
		enc, err := cryptoff.Encrypt(sessShared, data)
		if err != nil {
			return nil, fmt.Errorf("encrypting message: %w", err)
		}
		return &npb.SerializedStuff{Content: enc}, nil
	}

	for {
		req, err := server.Recv()
		if err != nil {
			return logErrorf(codes.Internal, "reading server request: %v", err)
		}
		decrypted, err := decryptReq(req)
		if err != nil {
			return logErrorf(codes.InvalidArgument, "could not decrypt message: %v", err)
		}
		resp, err := encryptResp(decrypted)
		if err != nil {
			return logErrorf(codes.Internal, "could not encrypt response: %v", err)
		}
		if err := server.Send(resp); err != nil {
			return logErrorf(codes.Internal, "could not send response: %v", err)
		}
	}
}

func logErrorf(code codes.Code, fmt string, values ...interface{}) error {
	err := status.Errorf(code, fmt, values...)
	zap.S().Errorf("%v", err)
	return err
}
