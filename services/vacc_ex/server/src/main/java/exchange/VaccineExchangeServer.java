package exchange;

import io.grpc.Server;
import io.grpc.ServerBuilder;
import io.grpc.protobuf.services.ProtoReflectionService;

import java.io.IOException;
import java.util.concurrent.TimeUnit;
import java.util.logging.Logger;

class VaccineExchangeServer {
    private static final Logger logger = Logger.getLogger(VaccineExchangeServer.class.getName());

    private final int listenPort;
    private final Server server;

    /**
     * Create a RouteGuide server using serverBuilder as a base and features as data.
     */
    VaccineExchangeServer(int port, VaccineExchangeRpc service) {
        listenPort = port;
        server = ServerBuilder.forPort(port).addService(service).addService(ProtoReflectionService.newInstance()).build();
    }

    void start() throws IOException {
        server.start();
        logger.info("Server started, listening on " + listenPort);
        Runtime.getRuntime().addShutdownHook(new Thread() {
            @Override
            public void run() {
                // Use stderr here since the logger may have been reset by its JVM shutdown hook.
                System.err.println("*** shutting down gRPC server since JVM is shutting down");
                try {
                    VaccineExchangeServer.this.stop();
                } catch (InterruptedException e) {
                    e.printStackTrace(System.err);
                }
                System.err.println("*** server shut down");
            }
        });
    }

    private void stop() throws InterruptedException {
        if (server != null) {
            server.shutdown().awaitTermination(30, TimeUnit.SECONDS);
        }
    }

    public void blockUntilShutdown() throws InterruptedException {
        if (server != null) {
            server.awaitTermination();
        }
    }
}
