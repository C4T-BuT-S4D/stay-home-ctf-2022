package storage

import (
	"context"
	"fmt"
	"time"

	"github.com/dgraph-io/badger/v3"
	"github.com/genjidb/genji"
	"github.com/genjidb/genji/document"
	_ "github.com/genjidb/genji/driver"
	"github.com/genjidb/genji/engine/badgerengine"
	"github.com/genjidb/genji/types"
	"github.com/google/uuid"
)

const (
	maxListSize = 100
)

func New(ctx context.Context, path string) (*Storage, error) {
	engine, err := badgerengine.NewEngine(badger.DefaultOptions(path))
	if err != nil {
		return nil, fmt.Errorf("opening badger file %s: %w", path, err)
	}

	db, err := genji.New(ctx, engine)
	if err != nil {
		return nil, fmt.Errorf("creating db: %w", err)
	}

	s := &Storage{db: db}
	if err := s.initTables(); err != nil {
		return nil, fmt.Errorf("initializing tables: %w", err)
	}
	return s, nil
}

type Storage struct {
	db *genji.DB
}

func (s *Storage) Add(user, content, name string) (*Document, error) {
	doc := Document{
		ID:        fmt.Sprintf("%s-%s", name, uuid.New()),
		User:      user,
		Content:   content,
		CreatedAt: time.Now(),
	}
	if err := s.db.Exec(`INSERT INTO documents VALUES ?`, &doc); err != nil {
		return nil, fmt.Errorf("inserting document for user %s: %w", user, err)
	}
	return &doc, nil
}

func (s *Storage) Get(id string) (*Document, error) {
	raw, err := s.db.QueryDocument(`SELECT * FROM documents WHERE id = ?`, id)
	if err != nil {
		return nil, fmt.Errorf("fetching document: %w", err)
	}

	var doc Document
	if err := document.StructScan(raw, &doc); err != nil {
		return nil, fmt.Errorf("decoding document: %w", err)
	}
	return &doc, nil
}

func (s *Storage) List(user string) ([]Document, error) {
	q := fmt.Sprintf(`SELECT * FROM documents WHERE user = ? ORDER BY created_at DESC LIMIT %d`, maxListSize)
	curs, err := s.db.Query(q, user)
	if err != nil {
		return nil, fmt.Errorf("fetching documents for user %s: %w", user, err)
	}
	//goland:noinspection GoUnhandledErrorResult
	defer curs.Close()

	var docs []Document
	if err := curs.Iterate(func(d types.Document) error {
		var doc Document
		if err := document.StructScan(d, &doc); err != nil {
			return fmt.Errorf("decoding document: %w", err)
		}
		docs = append(docs, doc)
		return nil
	}); err != nil {
		return nil, fmt.Errorf("iterating documents for user %s: %w", user, err)
	}
	return docs, nil
}

func (s *Storage) Close() error {
	if err := s.db.Close(); err != nil {
		return fmt.Errorf("closing db: %w", err)
	}
	return nil
}

func (s *Storage) initTables() error {
	if err := s.db.Exec(`CREATE TABLE IF NOT EXISTS documents`); err != nil {
		return fmt.Errorf("creating documents table: %w", err)
	}
	if err := s.db.Exec(`CREATE UNIQUE INDEX IF NOT EXISTS documents_id_idx ON documents (id)`); err != nil {
		return fmt.Errorf("creating id documents index: %w", err)
	}
	if err := s.db.Exec(`CREATE INDEX IF NOT EXISTS documents_user_idx ON documents (user)`); err != nil {
		return fmt.Errorf("creating user documents index: %w", err)
	}
	return nil
}
