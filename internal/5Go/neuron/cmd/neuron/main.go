package main

import (
	"context"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"neuron/internal/cleaner"
	"neuron/internal/storage"

	"go.uber.org/zap"
	"google.golang.org/grpc"
	"google.golang.org/grpc/reflection"

	"neuron/internal/service"
	npb "neuron/interop"
)

func main() {
	logger := setupLogger()

	store, err := storage.New(context.Background(), "data")
	if err != nil {
		logger.Fatalf("Failed to create storage: %v", err)
	}

	// 30m max age
	clean := cleaner.New(store, time.Minute, time.Minute*30)

	srv := service.NewNeuronService(store)
	s := grpc.NewServer()

	reflection.Register(s)
	npb.RegisterNeuronAPIServer(s, srv)

	lis, err := net.Listen("tcp", "0.0.0.0:5005")
	if err != nil {
		logger.Fatalf("Failed to listen: %v", err)
	}

	go func() {
		logger.Infof("Serving API on %v", "0.0.0.0:5005")
		if err := s.Serve(lis); err != nil {
			logger.Fatalf("Error serving gRPC API: %v", err)
		}
	}()

	logger.Infof("Starting old docs cleaner")
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	clean.Start(ctx)

	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)
	<-c

	logger.Infof("Stopping cleaner")
	cancel()
	sdCtx, sdCancel := context.WithTimeout(context.Background(), time.Second*3)
	defer sdCancel()
	if err := clean.Wait(sdCtx); err != nil {
		logger.Fatalf("Error shutting waiting for cleaner: %v", err)
	}

	logger.Info("Shutting down the API")
	s.GracefulStop()
}

func setupLogger() *zap.SugaredLogger {
	logger, err := zap.NewDevelopment()
	if err != nil {
		log.Fatalf("Error initializing logger: %v", err)
	}
	logger = logger.WithOptions(zap.AddStacktrace(zap.ErrorLevel))
	zap.ReplaceGlobals(logger)
	return logger.Sugar()
}
