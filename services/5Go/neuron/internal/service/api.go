package service

import (
	"context"
	"errors"
	"fmt"
	"io"

	"neuron/internal/storage"

	gerrs "github.com/genjidb/genji/errors"
	"go.uber.org/zap"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/types/known/emptypb"

	"neuron/internal/cryptoff"
	npb "neuron/interop"
)

// Empty buffers are not OK...
const (
	minimumDataLength = 5
)

func NewNeuronService(s *storage.Storage) *NeuronService {
	return &NeuronService{
		storage: s,
	}
}

type NeuronService struct {
	npb.UnimplementedNeuronAPIServer
	storage *storage.Storage
}

func (s *NeuronService) Ping(context.Context, *emptypb.Empty) (*emptypb.Empty, error) {
	return &emptypb.Empty{}, nil
}

func (s *NeuronService) Echo(server npb.NeuronAPI_EchoServer) error {
	shared, err := s.handleHandshake(server)
	if err != nil {
		return err
	}
	for {
		req, err := server.Recv()
		if errors.Is(err, io.EOF) {
			return nil
		}
		if err != nil {
			return logErrorf(codes.InvalidArgument, "reading server request: %v", err)
		}
		decrypted, err := decrypt(shared, req)
		if err != nil {
			return logErrorf(codes.InvalidArgument, "decrypting message: %v", err)
		}
		resp, err := encrypt(shared, decrypted)
		if err != nil {
			return logErrorf(codes.Internal, "marshalling response: %v", err)
		}
		if err := server.Send(resp); err != nil {
			return logErrorf(codes.Internal, "could not send response: %v", err)
		}
	}
}

func (s *NeuronService) Session(server npb.NeuronAPI_SessionServer) error {
	shared, err := s.handleHandshake(server)
	if err != nil {
		return err
	}
	for {
		req, err := server.Recv()
		if errors.Is(err, io.EOF) {
			return nil
		}
		if err != nil {
			return logErrorf(codes.InvalidArgument, "reading server request: %v", err)
		}
		decrypted, err := decrypt(shared, req)
		if err != nil {
			return logErrorf(codes.InvalidArgument, "decrypting message: %v", err)
		}

		var rawInternalReq npb.Request
		if err := proto.Unmarshal(decrypted, &rawInternalReq); err != nil {
			return logErrorf(codes.InvalidArgument, "invalid request: %v", err)
		}
		var resp proto.Message
		switch internalRequest := rawInternalReq.InternalRequest.(type) {
		case *npb.Request_Add:
			resp, err = s.handleAdd(internalRequest.Add)
		case *npb.Request_Get:
			resp, err = s.handleGet(internalRequest.Get)
		case *npb.Request_List:
			resp, err = s.handleList(internalRequest.List)
		default:
			return logErrorf(codes.Unimplemented, "unknown request type received: %v", rawInternalReq.InternalRequest)
		}
		if err != nil {
			return err
		}
		respContent, err := proto.Marshal(resp)
		if err != nil {
			return logErrorf(codes.Internal, "marshalling response: %v", err)
		}
		encResp, err := encrypt(shared, respContent)
		if err != nil {
			return logErrorf(codes.Internal, "encrypting response: %v", err)
		}
		if err := server.Send(encResp); err != nil {
			return logErrorf(codes.Internal, "sending response: %v", err)
		}
	}
}

func (s *NeuronService) handleHandshake(server npb.NeuronAPI_EchoServer) ([]byte, error) {
	im, err := server.Recv()
	if err != nil {
		return nil, logErrorf(codes.InvalidArgument, "reading initial message: %v", err)
	}

	sessSecret, err := cryptoff.GenerateKey()
	if err != nil {
		return nil, logErrorf(codes.Internal, "generating session private key: %v", err)
	}
	sessShared, err := cryptoff.GenerateShared(sessSecret, im.Content)
	if err != nil {
		return nil, logErrorf(codes.InvalidArgument, "generating session secret: %v", err)
	}
	var parsedSecret npb.AsymmetricKey
	if err := proto.Unmarshal(sessSecret, &parsedSecret); err != nil {
		return nil, logErrorf(codes.Internal, "unmarshalling session secret: %v", err)
	}
	if err := server.Send(parsedSecret.PublicKey); err != nil {
		return nil, logErrorf(codes.Internal, "sending public key: %v", err)
	}
	return sessShared, nil
}

func (s *NeuronService) handleAdd(req *npb.AddDocumentRequest) (*npb.Document, error) {
	if len(req.User) < minimumDataLength {
		return nil, logErrorf(codes.InvalidArgument, "user is too short")
	}
	if len(req.Name) < minimumDataLength {
		return nil, logErrorf(codes.InvalidArgument, "name is too short")
	}
	if len(req.Content) < minimumDataLength {
		return nil, logErrorf(codes.InvalidArgument, "content is too short")
	}

	doc, err := s.storage.Add(req.User, req.Content, req.Name)
	if err != nil {
		return nil, logErrorf(codes.Internal, "adding document to storage: %v", err)
	}
	return doc.ToProto(), nil
}

func (s *NeuronService) handleGet(req *npb.GetDocumentRequest) (*npb.Document, error) {
	if len(req.Id) < minimumDataLength {
		return nil, logErrorf(codes.InvalidArgument, "id is too short")
	}
	doc, err := s.storage.Get(req.Id)
	if err != nil {
		if errors.Is(err, gerrs.ErrDocumentNotFound) {
			return nil, logErrorf(codes.NotFound, "document not found")
		}
		return nil, logErrorf(codes.Internal, "getting data: %v", err)
	}
	return doc.ToProto(), nil
}

func (s *NeuronService) handleList(req *npb.ListDocumentsRequest) (*npb.ListDocumentsResponse, error) {
	if len(req.User) < minimumDataLength {
		return nil, logErrorf(codes.InvalidArgument, "user is too short")
	}
	docs, err := s.storage.List(req.User)
	if err != nil {
		return nil, logErrorf(codes.Internal, "listing user documents: %v", err)
	}
	resp := &npb.ListDocumentsResponse{
		Documents: make([]*npb.Document, 0, len(docs)),
	}
	for _, doc := range docs {
		resp.Documents = append(resp.Documents, doc.ToProto())
	}
	return resp, nil
}

func decrypt(shared []byte, stuff *npb.SerializedStuff) ([]byte, error) {
	data, err := cryptoff.Decrypt(shared, stuff.GetContent())
	if err != nil {
		return nil, fmt.Errorf("decrypting message: %w", err)
	}
	return data, nil
}

func encrypt(shared, data []byte) (*npb.SerializedStuff, error) {
	enc, err := cryptoff.Encrypt(shared, data)
	if err != nil {
		return nil, fmt.Errorf("encrypting message: %w", err)
	}
	return &npb.SerializedStuff{Content: enc}, nil
}

func logErrorf(code codes.Code, fmt string, values ...interface{}) error {
	err := status.Errorf(code, fmt, values...)
	if code == codes.Internal {
		zap.S().Errorf("%v", err)
	} else {
		zap.S().Warnf("%v", err)
	}
	return err
}
