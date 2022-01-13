package service

import (
	"context"
	"net"
	"os"
	"strings"
	"testing"

	"neuron/internal/storage"

	"github.com/stretchr/testify/require"
	"go.uber.org/zap"
	"go.uber.org/zap/zaptest"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"google.golang.org/grpc/test/bufconn"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/types/known/emptypb"

	"neuron/internal/cryptoff"
	npb "neuron/interop"
)

const bufSize = 1024 * 1024

var lis *bufconn.Listener

const (
	user1 = "some user"
	user2 = "another user"
	user3 = "empty user"

	content1 = "some content"
	content2 = "another content"

	name1 = "name1"
	name2 = "name2"
	name3 = "name3"
)

func setup(t *testing.T) func() {
	setupLogger(t)

	path, err := os.MkdirTemp("", "testdb")
	require.NoError(t, err)

	store, err := storage.New(context.Background(), path)
	if err != nil {
		require.NoError(t, os.RemoveAll(path))
	}
	require.NoError(t, err)

	lis = bufconn.Listen(bufSize)
	s := grpc.NewServer()
	npb.RegisterNeuronAPIServer(s, NewNeuronService(store))
	go func() {
		require.NoError(t, s.Serve(lis))
	}()

	return func() {
		require.NoError(t, store.Close())
		require.NoError(t, os.RemoveAll(path))
	}
}

func bufDialer(context.Context, string) (net.Conn, error) {
	return lis.Dial()
}

func setupLogger(t *testing.T) {
	logger := zaptest.NewLogger(t, zaptest.Level(zap.DebugLevel))
	zap.ReplaceGlobals(logger)
}

func TestPing(t *testing.T) {
	cleanup := setup(t)
	defer cleanup()

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

func TestEcho(t *testing.T) {
	cleanup := setup(t)
	defer cleanup()

	ctx := context.Background()
	conn, err := grpc.DialContext(ctx, "bufnet", grpc.WithContextDialer(bufDialer), grpc.WithInsecure())
	require.NoError(t, err, "dialing bufnet")
	defer func() {
		require.NoError(t, conn.Close())
	}()

	client := npb.NewNeuronAPIClient(conn)
	sessClient, err := client.Echo(ctx)
	require.NoError(t, err, "session init returned error")

	sessSecret, err := cryptoff.GenerateKey()
	require.NoError(t, err, "generating session private key")
	var parsedSecret npb.AsymmetricKey
	require.NoError(t, proto.Unmarshal(sessSecret, &parsedSecret), "unmarshalling secret")
	require.NoError(t, sessClient.Send(parsedSecret.PublicKey), "sending public key")

	resp, err := sessClient.Recv()
	require.NoError(t, err, "receiving server pubkey")

	sessShared, err := cryptoff.GenerateShared(sessSecret, resp.Content)
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
		decMsg, err := cryptoff.Decrypt(sessShared, resp.Content)
		require.NoError(t, err, "decrypting server response")
		require.Equal(t, message, string(decMsg), "incorrect decoded message")
	}
}

func TestSession(t *testing.T) {
	cleanup := setup(t)
	defer cleanup()

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
	require.NoError(t, sessClient.Send(parsedSecret.PublicKey), "sending public key")

	resp, err := sessClient.Recv()
	require.NoError(t, err, "receiving server pubkey")

	sessShared, err := cryptoff.GenerateShared(sessSecret, resp.Content)
	require.NoError(t, err, "generating client shared key")
	t.Logf("Session key: %v", sessShared)

	send := func(m *npb.Request) {
		content, err := proto.Marshal(m)
		require.NoError(t, err, "marshalling message")
		encMsg, err := cryptoff.Encrypt(sessShared, content)
		require.NoError(t, err, "encrypting message")
		t.Logf("Encrypted message: %v", encMsg)
		req := npb.SerializedStuff{Content: encMsg}
		require.NoError(t, sessClient.Send(&req), "sending request")
	}
	recv := func(m proto.Message) {
		resp, err := sessClient.Recv()
		require.NoError(t, err, "reading server response")
		decMsg, err := cryptoff.Decrypt(sessShared, resp.Content)
		require.NoError(t, err, "decrypting server response")
		require.NoError(t, proto.Unmarshal(decMsg, m), "unmarshalling response")
	}

	send(
		&npb.Request{
			InternalRequest: &npb.Request_Add{
				Add: &npb.AddDocumentRequest{
					User:    user1,
					Content: content1,
					Name:    name1,
				},
			},
		},
	)
	var doc1 npb.Document
	recv(&doc1)
	require.Equal(t, user1, doc1.User)
	require.Equal(t, content1, doc1.Content)
	require.True(t, strings.HasPrefix(doc1.Id, name1))

	send(
		&npb.Request{
			InternalRequest: &npb.Request_Get{
				Get: &npb.GetDocumentRequest{
					Id: doc1.Id,
				},
			},
		},
	)
	var dbDoc1 npb.Document
	recv(&dbDoc1)
	requireDocsEqual(t, &doc1, &dbDoc1)

	send(
		&npb.Request{
			InternalRequest: &npb.Request_Add{
				Add: &npb.AddDocumentRequest{
					User:    user1,
					Content: content2,
					Name:    name2,
				},
			},
		},
	)
	var doc2 npb.Document
	recv(&doc2)

	send(
		&npb.Request{
			InternalRequest: &npb.Request_Add{
				Add: &npb.AddDocumentRequest{
					User:    user2,
					Content: content1,
					Name:    name3,
				},
			},
		},
	)
	var doc3 npb.Document
	recv(&doc3)

	send(
		&npb.Request{
			InternalRequest: &npb.Request_List{
				List: &npb.ListDocumentsRequest{
					User: user1,
				},
			},
		},
	)
	var docs1 npb.ListDocumentsResponse
	recv(&docs1)
	require.Len(t, docs1.Documents, 2)
	requireDocsEqual(t, &doc2, docs1.Documents[0])
	requireDocsEqual(t, &doc1, docs1.Documents[1])

	send(
		&npb.Request{
			InternalRequest: &npb.Request_List{
				List: &npb.ListDocumentsRequest{
					User: user2,
				},
			},
		},
	)
	var docs2 npb.ListDocumentsResponse
	recv(&docs2)
	require.Len(t, docs2.Documents, 1)
	requireDocsEqual(t, &doc3, docs2.Documents[0])

	send(
		&npb.Request{
			InternalRequest: &npb.Request_List{
				List: &npb.ListDocumentsRequest{
					User: user3,
				},
			},
		},
	)
	var docs3 npb.ListDocumentsResponse
	recv(&docs3)
	require.Len(t, docs3.Documents, 0)
}

func TestShorts(t *testing.T) {
	tests := []struct {
		name string
		req  *npb.Request
	}{
		{
			"list_user",
			&npb.Request{
				InternalRequest: &npb.Request_List{
					List: &npb.ListDocumentsRequest{
						User: "shrt",
					},
				},
			},
		},
		{
			"add_user",
			&npb.Request{
				InternalRequest: &npb.Request_Add{
					Add: &npb.AddDocumentRequest{
						User:    "shrt",
						Content: content1,
						Name:    name3,
					},
				},
			},
		},
		{
			"add_content",
			&npb.Request{
				InternalRequest: &npb.Request_Add{
					Add: &npb.AddDocumentRequest{
						User:    user1,
						Content: "shrt",
						Name:    name3,
					},
				},
			},
		},
		{
			"add_name",
			&npb.Request{
				InternalRequest: &npb.Request_Add{
					Add: &npb.AddDocumentRequest{
						User:    user1,
						Content: content1,
						Name:    "shrt",
					},
				},
			},
		},
		{
			"get_id",
			&npb.Request{
				InternalRequest: &npb.Request_Get{
					Get: &npb.GetDocumentRequest{
						Id: "shrt",
					},
				},
			},
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			cleanup := setup(t)
			defer cleanup()

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
			require.NoError(t, sessClient.Send(parsedSecret.PublicKey), "sending public key")

			resp, err := sessClient.Recv()
			require.NoError(t, err, "receiving server pubkey")

			sessShared, err := cryptoff.GenerateShared(sessSecret, resp.Content)
			require.NoError(t, err, "generating client shared key")
			t.Logf("Session key: %v", sessShared)

			send := func(m *npb.Request) {
				content, err := proto.Marshal(m)
				require.NoError(t, err, "marshalling message")
				encMsg, err := cryptoff.Encrypt(sessShared, content)
				require.NoError(t, err, "encrypting message")
				t.Logf("Encrypted message: %v", encMsg)
				req := npb.SerializedStuff{Content: encMsg}
				require.NoError(t, sessClient.Send(&req), "sending request")
			}

			send(tt.req)
			_, err = sessClient.Recv()
			requireGRPCCode(t, err, codes.InvalidArgument)
		})
	}
}

func TestMalformedHandshake(t *testing.T) {
	cleanup := setup(t)
	defer cleanup()

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
	require.NoError(t, sessClient.Send(parsedSecret.PublicKey), "sending public key")

	_, err = sessClient.Recv()
	require.Error(t, err, "should return error")
}

func TestMalformedEncryptedPacket(t *testing.T) {
	cleanup := setup(t)
	defer cleanup()

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
	require.NoError(t, sessClient.Send(parsedSecret.PublicKey), "sending public key")

	resp, err := sessClient.Recv()
	require.NoError(t, err, "receiving server pubkey")

	sessShared, err := cryptoff.GenerateShared(sessSecret, resp.Content)
	require.NoError(t, err, "generating client shared key")
	t.Logf("Session key: %v", sessShared)

	message := strings.Repeat("kek", 10)
	t.Logf("Sending the request with message: %s", message)

	encMsg, err := cryptoff.Encrypt(sessShared, []byte(message))
	require.NoError(t, err, "encrypting message")

	// break the encrypted message
	encMsg = encMsg[:len(encMsg)-3]
	req := npb.SerializedStuff{Content: encMsg}
	require.NoError(t, sessClient.Send(&req), "sending request")
	_, err = sessClient.Recv()
	require.Error(t, err, "should return error")
}

func requireDocsEqual(t *testing.T, expected, actual *npb.Document) {
	t.Helper()
	require.Equal(t, expected.Id, actual.Id)
	require.Equal(t, expected.User, actual.User)
	require.Equal(t, expected.Content, actual.Content)
	require.Equal(t, expected.CreatedAt.AsTime().UnixMicro(), actual.CreatedAt.AsTime().UnixMicro())
}

func requireGRPCCode(t *testing.T, err error, code codes.Code) {
	t.Helper()
	require.Error(t, err)
	st, ok := status.FromError(err)
	require.True(t, ok)
	require.Equal(t, code, st.Code())
}
