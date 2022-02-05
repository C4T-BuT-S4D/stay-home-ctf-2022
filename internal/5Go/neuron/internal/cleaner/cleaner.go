package cleaner

import (
	"context"
	"fmt"
	"time"

	"neuron/internal/storage"

	"go.uber.org/zap"
)

func New(s *storage.Storage, interval, age time.Duration) *Cleaner {
	return &Cleaner{
		storage:  s,
		interval: interval,
		age:      age,
		done:     make(chan struct{}),
	}
}

type Cleaner struct {
	storage  *storage.Storage
	interval time.Duration
	age      time.Duration

	done chan struct{}
}

func (c *Cleaner) Start(ctx context.Context) {
	defer close(c.done)
	t := time.NewTicker(c.interval)
	defer t.Stop()
	for {
		select {
		case <-t.C:
			zap.S().Infof("Running cleaner iteration")
			if err := c.run(); err != nil {
				zap.S().Errorf("Error cleaning old documents: %v", err)
			}
		case <-ctx.Done():
			zap.S().Infof("Stopping cleaner")
			return
		}
	}
}

func (c *Cleaner) Wait(ctx context.Context) error {
	select {
	case <-c.done:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

func (c *Cleaner) run() error {
	cutoff := time.Now().Add(-c.age)
	if err := c.storage.DeleteOld(cutoff); err != nil {
		return fmt.Errorf("removing documents older than %v: %w", cutoff, err)
	}
	return nil
}
