package storage

import (
	"fmt"
	"time"

	npb "neuron/interop"

	"google.golang.org/protobuf/types/known/timestamppb"
)

type Document struct {
	ID        string
	User      string
	Content   string
	CreatedAt time.Time
}

func (d *Document) String() string {
	return fmt.Sprintf(
		"Document(id=%s, user=%s, content=%s)",
		d.ID,
		d.User,
		d.Content,
	)
}

func (d *Document) ToProto() *npb.Document {
	return &npb.Document{
		Id:        d.ID,
		User:      d.User,
		Content:   d.Content,
		CreatedAt: timestamppb.New(d.CreatedAt),
	}
}
