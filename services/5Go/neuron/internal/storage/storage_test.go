package storage

import (
	"context"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/stretchr/testify/require"
)

func createStorage(t *testing.T) (*Storage, func()) {
	t.Helper()

	path, err := os.MkdirTemp("", "testdb")
	require.NoError(t, err)
	t.Logf("Created db at %v", path)

	s, err := New(context.Background(), path)
	if err != nil {
		require.NoError(t, os.RemoveAll(path))
	}
	require.NoError(t, err)
	return s, func() {
		require.NoError(t, s.Close())
		require.NoError(t, os.RemoveAll(path))
	}
}

func TestStorage(t *testing.T) {
	s, cleanup := createStorage(t)
	defer cleanup()

	const (
		user1 = "some user"
		user2 = "another user"
	)

	const (
		content1 = "some content"
		content2 = "another content"
	)

	const (
		name1 = "name1"
		name2 = "name2"
		name3 = "name3"
	)

	doc1, err := s.Add(user1, content1, name1)
	require.NoError(t, err)
	require.Equal(t, user1, doc1.User)
	require.Equal(t, content1, doc1.Content)
	require.True(t, strings.HasPrefix(doc1.ID, name1))

	dbDoc1, err := s.Get(doc1.ID)
	require.NoError(t, err)
	requireDocsEqual(t, doc1, dbDoc1)

	docs, err := s.List(user1)
	require.NoError(t, err)
	require.Len(t, docs, 1)
	requireDocsEqual(t, doc1, &docs[0])

	time.Sleep(2 * time.Second)

	doc2, err := s.Add(user1, content2, name2)
	require.NoError(t, err)

	dbDoc2, err := s.Get(doc2.ID)
	require.NoError(t, err)
	requireDocsEqual(t, doc2, dbDoc2)

	docs, err = s.List(user1)
	require.NoError(t, err)
	require.Len(t, docs, 2)
	requireDocsEqual(t, doc2, &docs[1])
	requireDocsEqual(t, doc1, &docs[0])

	doc3, err := s.Add(user2, content1, name3)
	require.NoError(t, err)

	docs, err = s.List(user1)
	require.NoError(t, err)
	require.Len(t, docs, 2)

	docs, err = s.List(user2)
	require.NoError(t, err)
	require.Len(t, docs, 1)
	requireDocsEqual(t, doc3, &docs[0])

	cutoff := dbDoc1.CreatedAt.Add(time.Second)
	require.NoError(t, s.DeleteOld(cutoff))
	docs, err = s.List(user1)
	require.NoError(t, err)
	require.Len(t, docs, 1)
	requireDocsEqual(t, doc2, &docs[0])
}

func requireDocsEqual(t *testing.T, expected, actual *Document) {
	t.Helper()
	require.Equal(t, expected.ID, actual.ID)
	require.Equal(t, expected.User, actual.User)
	require.Equal(t, expected.Content, actual.Content)
	require.Equal(t, expected.CreatedAt.UnixMicro(), actual.CreatedAt.UnixMicro())
}
