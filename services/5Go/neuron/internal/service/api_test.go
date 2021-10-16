package service

import (
	"context"
	"log"
	"net"
	"strings"
	"testing"

	"github.com/stretchr/testify/require"
	"go.uber.org/zap"
	"go.uber.org/zap/zaptest"
	"google.golang.org/grpc"
	"google.golang.org/grpc/test/bufconn"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/types/known/emptypb"

	"neuron/internal/cryptoff"
	npb "neuron/interop"
)

const bufSize = 1024 * 1024

var lis *bufconn.Listener

func init() {
	lis = bufconn.Listen(bufSize)
	s := grpc.NewServer()
	npb.RegisterNeuronAPIServer(s, NewNeuronService())
	go func() {
		if err := s.Serve(lis); err != nil {
			log.Fatalf("Server exited with error: %v", err)
		}
	}()
}

func bufDialer(context.Context, string) (net.Conn, error) {
	return lis.Dial()
}

func setupLogger(t *testing.T) {
	logger := zaptest.NewLogger(t, zaptest.Level(zap.DebugLevel))
	zap.ReplaceGlobals(logger)
}

func TestPing(t *testing.T) {
	setupLogger(t)
	ctx := context.Background()
	conn, err := grpc.DialContext(ctx, "bufnet", grpc.WithContextDialer(bufDialer), grpc.WithInsecure())
	require.NoError(t, err, "Dialing bufnet")
	defer func() {
		require.NoError(t, conn.Close())
	}()
	client := npb.NewNeuronAPIClient(conn)
	resp, err := client.Ping(ctx, &emptypb.Empty{})
	require.NoError(t, err, "Ping returned error")
	t.Logf("Response: %+v", resp)
}

func TestSession(t *testing.T) {
	setupLogger(t)
	ctx := context.Background()
	conn, err := grpc.DialContext(ctx, "bufnet", grpc.WithContextDialer(bufDialer), grpc.WithInsecure())
	require.NoError(t, err, "dialing bufnet")
	defer func() {
		require.NoError(t, conn.Close())
	}()

	client := npb.NewNeuronAPIClient(conn)
	sessClient, err := client.Session(ctx)
	require.NoError(t, err, "session init returned error")

	sessSecret, err := cryptoff.GenerateKey()
	require.NoError(t, err, "generating session private key")
	var parsedSecret npb.AsymmetricKey
	require.NoError(t, proto.Unmarshal(sessSecret, &parsedSecret), "unmarshalling secret")
	require.NoError(t, sessClient.Send(parsedSecret.GetPublicKey()), "sending public key")

	resp, err := sessClient.Recv()
	require.NoError(t, err, "receiving server pubkey")

	sessShared, err := cryptoff.GenerateShared(sessSecret, resp.GetContent())
	require.NoError(t, err, "generating client shared key")
	t.Logf("Session key: %v", sessShared)

	for i := 0; i < 10; i++ {
		message := strings.Repeat("kek", i+1)
		t.Logf("Sending the request with message: %s", message)
		encMsg, err := cryptoff.Encrypt(sessShared, []byte(message))
		require.NoError(t, err, "encrypting message")
		t.Logf("Encrypted message: %v", encMsg)
		req := npb.SerializedStuff{Content: encMsg}
		require.NoError(t, sessClient.Send(&req), "sending request")
		resp, err := sessClient.Recv()
		require.NoError(t, err, "reading server response")
		require.Equal(t, encMsg, resp.GetContent(), "invalid response from server")
	}
}

func TestMalformedHandshake(t *testing.T) {
	setupLogger(t)
	ctx := context.Background()
	conn, err := grpc.DialContext(ctx, "bufnet", grpc.WithContextDialer(bufDialer), grpc.WithInsecure())
	require.NoError(t, err, "dialing bufnet")
	defer func() {
		require.NoError(t, conn.Close())
	}()

	client := npb.NewNeuronAPIClient(conn)
	sessClient, err := client.Session(ctx)
	require.NoError(t, err, "session init returned error")

	sessSecret, err := cryptoff.GenerateKey()
	require.NoError(t, err, "generating session private key")
	var parsedSecret npb.AsymmetricKey
	require.NoError(t, proto.Unmarshal(sessSecret, &parsedSecret), "unmarshalling secret")

	// Break the public key.
	parsedSecret.PublicKey.Content = []byte("kek")
	require.NoError(t, sessClient.Send(parsedSecret.GetPublicKey()), "sending public key")

	_, err = sessClient.Recv()
	require.Error(t, err, "should return error")
}

func TestMalformedEncryptedPacket(t *testing.T) {
	setupLogger(t)
	ctx := context.Background()
	conn, err := grpc.DialContext(ctx, "bufnet", grpc.WithContextDialer(bufDialer), grpc.WithInsecure())
	require.NoError(t, err, "dialing bufnet")
	defer func() {
		require.NoError(t, conn.Close())
	}()

	client := npb.NewNeuronAPIClient(conn)
	sessClient, err := client.Session(ctx)
	require.NoError(t, err, "session init returned error")

	sessSecret, err := cryptoff.GenerateKey()
	require.NoError(t, err, "generating session private key")
	var parsedSecret npb.AsymmetricKey
	require.NoError(t, proto.Unmarshal(sessSecret, &parsedSecret), "unmarshalling secret")
	require.NoError(t, sessClient.Send(parsedSecret.GetPublicKey()), "sending public key")

	resp, err := sessClient.Recv()
	require.NoError(t, err, "receiving server pubkey")

	sessShared, err := cryptoff.GenerateShared(sessSecret, resp.GetContent())
	require.NoError(t, err, "generating client shared key")
	t.Logf("Session key: %v", sessShared)

	message := strings.Repeat("kek", 10)
	t.Logf("Sending the request with message: %s", message)

	encMsg, err := cryptoff.Encrypt(sessShared, []byte(message))
	require.NoError(t, err, "encrypting message")

	// break the encrypted message
	encMsg = encMsg[:len(encMsg) - 3]
	req := npb.SerializedStuff{Content: encMsg}
	require.NoError(t, sessClient.Send(&req), "sending request")
	_, err = sessClient.Recv()
	require.Error(t, err, "should return error")
}
