package exchange;

import io.grpc.Status;
import io.grpc.StatusException;
import io.grpc.stub.StreamObserver;
import exchange.proto.Exchange.*;
import exchange.proto.VaccineExchangeGrpc;

import java.util.UUID;

public class VaccineExchangeRpc extends VaccineExchangeGrpc.VaccineExchangeImplBase {
    private final VaccineExchangeService service;

    public VaccineExchangeRpc(VaccineExchangeService srv) {
        super();
        service = srv;
    }

    private StatusException toStatusException(Exception e) {
        return new StatusException(Status.INTERNAL.withDescription(e.getMessage()));
    }

    @Override
    public void login(LoginRequest request, StreamObserver<LoginResponse> responseObserver) {
        try {
            String token = service.loginUser(request.getUserId(), request.getUserPassword());
            responseObserver.onNext(
                    LoginResponse
                            .newBuilder()
                            .setAuth(Auth.newBuilder()
                                    .setToken(token)
                                    .build())
                            .build()
            );
            responseObserver.onCompleted();
        } catch (Exception e) {
            responseObserver.onError(e);
        }
    }

    @Override
    public void register(RegisterRequest request, StreamObserver<RegisterResponse> responseObserver) {
        String userId = UUID.randomUUID().toString();
        String password = RandomHelper.getString(15);
        try {
            service.createUser(userId, password);
        } catch (Exception e) {
            responseObserver.onError(new StatusException(Status.ALREADY_EXISTS.withDescription(e.getMessage())));
            return;
        }

        responseObserver.onNext(RegisterResponse
                .newBuilder()
                .setUserId(userId)
                .setUserPassword(password)
                .build()
        );
        responseObserver.onCompleted();
    }

    public String getUserId(Auth auth, StreamObserver<?> observer) {
        try {
            return service.getUserId(auth.getToken());
        } catch (Exception e) {
            observer.onError(e);
            return null;
        }
    }

    @Override
    public void createVaccine(CreateVaccineRequest request, StreamObserver<CreateVaccineResponse> responseObserver) {
        String userId = getUserId(request.getAuth(), responseObserver);
        if (userId == null) {
            return;
        }

        try {
            responseObserver.onNext(CreateVaccineResponse
                    .newBuilder()
                    .setVaccine(service.createVaccine(userId, request))
                    .build()
            );
            responseObserver.onCompleted();

        } catch (StatusException e) {
            responseObserver.onError(e);
        } catch (Exception e) {
            responseObserver.onError(toStatusException(e));
        }
    }

    @Override
    public void buy(BuyRequest request, StreamObserver<BuyResponse> responseObserver) {
        String userId = getUserId(request.getAuth(), responseObserver);
        if (userId == null) {
            return;
        }

        try {
            VaccineInfo info = service.buy(userId, request.getStockId());
            responseObserver.onNext(BuyResponse.newBuilder().setRnaInfo(info.getRnaInfo()).build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            responseObserver.onError(toStatusException(e));
        }
    }


    @Override
    public void balance(BalanceRequest request, StreamObserver<BalanceResponse> responseObserver) {
        String userId = getUserId(request.getAuth(), responseObserver);
        if (userId == null) {
            return;
        }

        responseObserver.onNext(BalanceResponse.newBuilder().setBalance(service.getBalance(userId)).build());
        responseObserver.onCompleted();
    }

    @Override
    public void getPrice(PriceRequest request, StreamObserver<PriceResponse> responseObserver) {
        try {
            double price = service.getPrice(request.getStockId());
            responseObserver.onNext(PriceResponse.newBuilder().setPrice(price).build());
            responseObserver.onCompleted();
        } catch (Exception e) {
            responseObserver.onError(toStatusException(e));
        }
    }

    @Override
    public void list(ListRequest request, StreamObserver<ListResponse> responseObserver) {
        responseObserver.onNext(ListResponse.newBuilder().addAllVaccines(service.getLatestInfos()).build());
        responseObserver.onCompleted();
    }

    @Override
    public void getUserVaccine(GetUserVaccineRequest request, StreamObserver<GetUserVaccineResponse> responseObserver) {
        String userId = getUserId(request.getAuth(), responseObserver);
        if (userId == null) {
            return;
        }

        try {
            responseObserver.onNext(GetUserVaccineResponse
                    .newBuilder()
                    .setVaccine(service.getUserVaccine(userId))
                    .build()
            );
            responseObserver.onCompleted();
        } catch (StatusException e) {
            responseObserver.onError(e);
        } catch (Exception e) {
            responseObserver.onError(toStatusException(e));
        }
    }
}
