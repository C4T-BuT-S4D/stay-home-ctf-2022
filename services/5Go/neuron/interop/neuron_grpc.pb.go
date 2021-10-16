// Code generated by protoc-gen-go-grpc. DO NOT EDIT.

package interop

import (
	context "context"
	grpc "google.golang.org/grpc"
	codes "google.golang.org/grpc/codes"
	status "google.golang.org/grpc/status"
	emptypb "google.golang.org/protobuf/types/known/emptypb"
)

// This is a compile-time assertion to ensure that this generated file
// is compatible with the grpc package it is being compiled against.
const _ = grpc.SupportPackageIsVersion7

// NeuronAPIClient is the client API for NeuronAPI service.
//
// For semantics around ctx use and closing/ending streaming RPCs, please refer to https://pkg.go.dev/google.golang.org/grpc/?tab=doc#ClientConn.NewStream.
type NeuronAPIClient interface {
	Ping(ctx context.Context, in *emptypb.Empty, opts ...grpc.CallOption) (*emptypb.Empty, error)
	Session(ctx context.Context, opts ...grpc.CallOption) (NeuronAPI_SessionClient, error)
}

type neuronAPIClient struct {
	cc grpc.ClientConnInterface
}

func NewNeuronAPIClient(cc grpc.ClientConnInterface) NeuronAPIClient {
	return &neuronAPIClient{cc}
}

func (c *neuronAPIClient) Ping(ctx context.Context, in *emptypb.Empty, opts ...grpc.CallOption) (*emptypb.Empty, error) {
	out := new(emptypb.Empty)
	err := c.cc.Invoke(ctx, "/neuron.neuron.NeuronAPI/Ping", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *neuronAPIClient) Session(ctx context.Context, opts ...grpc.CallOption) (NeuronAPI_SessionClient, error) {
	stream, err := c.cc.NewStream(ctx, &_NeuronAPI_serviceDesc.Streams[0], "/neuron.neuron.NeuronAPI/Session", opts...)
	if err != nil {
		return nil, err
	}
	x := &neuronAPISessionClient{stream}
	return x, nil
}

type NeuronAPI_SessionClient interface {
	Send(*SerializedStuff) error
	Recv() (*SerializedStuff, error)
	grpc.ClientStream
}

type neuronAPISessionClient struct {
	grpc.ClientStream
}

func (x *neuronAPISessionClient) Send(m *SerializedStuff) error {
	return x.ClientStream.SendMsg(m)
}

func (x *neuronAPISessionClient) Recv() (*SerializedStuff, error) {
	m := new(SerializedStuff)
	if err := x.ClientStream.RecvMsg(m); err != nil {
		return nil, err
	}
	return m, nil
}

// NeuronAPIServer is the server API for NeuronAPI service.
// All implementations must embed UnimplementedNeuronAPIServer
// for forward compatibility
type NeuronAPIServer interface {
	Ping(context.Context, *emptypb.Empty) (*emptypb.Empty, error)
	Session(NeuronAPI_SessionServer) error
	mustEmbedUnimplementedNeuronAPIServer()
}

// UnimplementedNeuronAPIServer must be embedded to have forward compatible implementations.
type UnimplementedNeuronAPIServer struct {
}

func (UnimplementedNeuronAPIServer) Ping(context.Context, *emptypb.Empty) (*emptypb.Empty, error) {
	return nil, status.Errorf(codes.Unimplemented, "method Ping not implemented")
}
func (UnimplementedNeuronAPIServer) Session(NeuronAPI_SessionServer) error {
	return status.Errorf(codes.Unimplemented, "method Session not implemented")
}
func (UnimplementedNeuronAPIServer) mustEmbedUnimplementedNeuronAPIServer() {}

// UnsafeNeuronAPIServer may be embedded to opt out of forward compatibility for this service.
// Use of this interface is not recommended, as added methods to NeuronAPIServer will
// result in compilation errors.
type UnsafeNeuronAPIServer interface {
	mustEmbedUnimplementedNeuronAPIServer()
}

func RegisterNeuronAPIServer(s grpc.ServiceRegistrar, srv NeuronAPIServer) {
	s.RegisterService(&_NeuronAPI_serviceDesc, srv)
}

func _NeuronAPI_Ping_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(emptypb.Empty)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(NeuronAPIServer).Ping(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/neuron.neuron.NeuronAPI/Ping",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(NeuronAPIServer).Ping(ctx, req.(*emptypb.Empty))
	}
	return interceptor(ctx, in, info, handler)
}

func _NeuronAPI_Session_Handler(srv interface{}, stream grpc.ServerStream) error {
	return srv.(NeuronAPIServer).Session(&neuronAPISessionServer{stream})
}

type NeuronAPI_SessionServer interface {
	Send(*SerializedStuff) error
	Recv() (*SerializedStuff, error)
	grpc.ServerStream
}

type neuronAPISessionServer struct {
	grpc.ServerStream
}

func (x *neuronAPISessionServer) Send(m *SerializedStuff) error {
	return x.ServerStream.SendMsg(m)
}

func (x *neuronAPISessionServer) Recv() (*SerializedStuff, error) {
	m := new(SerializedStuff)
	if err := x.ServerStream.RecvMsg(m); err != nil {
		return nil, err
	}
	return m, nil
}

var _NeuronAPI_serviceDesc = grpc.ServiceDesc{
	ServiceName: "neuron.neuron.NeuronAPI",
	HandlerType: (*NeuronAPIServer)(nil),
	Methods: []grpc.MethodDesc{
		{
			MethodName: "Ping",
			Handler:    _NeuronAPI_Ping_Handler,
		},
	},
	Streams: []grpc.StreamDesc{
		{
			StreamName:    "Session",
			Handler:       _NeuronAPI_Session_Handler,
			ServerStreams: true,
			ClientStreams: true,
		},
	},
	Metadata: "neuron.proto",
}
