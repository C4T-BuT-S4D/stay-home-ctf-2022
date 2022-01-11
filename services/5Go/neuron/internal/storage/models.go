package gs

import (
	"fmt"
	"time"
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
