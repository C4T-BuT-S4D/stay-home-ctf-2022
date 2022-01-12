package cryptoff

import (
	"bytes"
	"strings"
	"testing"

	"github.com/stretchr/testify/require"
	"google.golang.org/protobuf/proto"

	npb "neuron/interop"
)

func TestE2EEncryption(t *testing.T) {
	shared := keyExchange(t)

	message := []byte(strings.Repeat("kek", 10))
	t.Logf("Encrypting message: %s", string(message))

	enc, err := Encrypt(shared, message)
	if err != nil {
		t.Fatalf("Error encrypting message: %v", err)
	}
	t.Logf("Encoded message: %v\n", enc)
	dec, err := Decrypt(shared, enc)
	if err != nil {
		t.Fatalf("Error decrypting message: %v", err)
	}
	t.Logf("Decrypted message: %v\n", string(dec))
	require.Equal(t, message, dec, "Invalid decrypted message")
}

func BenchmarkEncrypt(b *testing.B) {
	runBench := func(b *testing.B, message []byte) {
		shared := keyExchange(b)
		b.ResetTimer()
		for i := 0; i < b.N; i++ {
			if _, err := Encrypt(shared, message); err != nil {
				b.Fatalf("Error encrypting: %v", err)
			}
		}
	}
	b.Run("short string", func(b *testing.B) {
		runBench(b, []byte("kek"))
	})
	b.Run("medium string", func(b *testing.B) {
		runBench(b, bytes.Repeat([]byte("kek"), 20))
	})
	b.Run("long string", func(b *testing.B) {
		runBench(b, bytes.Repeat([]byte("kek"), 1000))
	})
	b.Run("extra long string", func(b *testing.B) {
		runBench(b, bytes.Repeat([]byte("kek"), 100000))
	})
}

func keyExchange(t testing.TB) []byte {
	t.Helper()

	aliceKey, err := GenerateKey()
	require.NoError(t, err)

	bobKey, err := GenerateKey()
	require.NoError(t, err)

	var aliceParsed, bobParsed npb.AsymmetricKey
	if err := proto.Unmarshal(aliceKey, &aliceParsed); err != nil {
		t.Fatalf("[ALICE] Error unmarshalling asymmetric key: %v", err)
	}
	t.Logf("[ALICE] Decoded key: %v\n", aliceParsed.PublicKey)

	if err := proto.Unmarshal(bobKey, &bobParsed); err != nil {
		t.Fatalf("[BOB] Error unmarshalling asymmetric key: %v", err)
	}
	t.Logf("[BOB] Decoded key: %v\n", bobParsed.PublicKey)

	aliceShared, err := GenerateShared(aliceKey, bobParsed.PublicKey.Content)
	require.NoError(t, err, "[ALICE] generating shared key")
	bobShared, err := GenerateShared(bobKey, aliceParsed.PublicKey.Content)
	require.NoError(t, err, "[BOB] generating shared key")
	require.Equal(t, aliceShared, bobShared, "Generated shared secrets are not equal")
	return aliceShared
}
