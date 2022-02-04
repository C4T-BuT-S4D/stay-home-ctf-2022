package exchange;

import com.google.common.base.Strings;
import com.google.common.util.concurrent.Striped;
import io.grpc.Status;
import io.grpc.StatusException;
import exchange.proto.Exchange.Vaccine;
import exchange.proto.Exchange.SellInfo;
import exchange.proto.Exchange.VaccineInfo;
import exchange.proto.Exchange.CreateVaccineRequest;
import exchange.proto.Exchange.ListVaccineInfo;

import java.util.List;
import java.util.UUID;
import java.util.concurrent.locks.Lock;

public class VaccineExchangeService {
    private final VaccineExchangeStorage storage;
    private static double defaultBalance = 5.0;
    private Striped<Lock> locks;
    private static long expireSeconds = 60 * 10;
    private static long fetchLastN = 250;

    public VaccineExchangeService(VaccineExchangeStorage store) {
        storage = store;
        locks = Striped.lock(4096);
    }


    String loginUser(String userId, String password) throws StatusException {
        String passwordDb = storage.findUserPassword(userId);
        if (Strings.isNullOrEmpty(passwordDb)) {
            throw new StatusException(Status.NOT_FOUND.withDescription("user not found"));
        }

        if (!passwordDb.equals(password)) {
            throw new StatusException(Status.FAILED_PRECONDITION.withDescription("invalid password provided"));
        }

        String token = RandomHelper.getString(30);

        storage.saveToken(userId, token, expireSeconds);

        return token;
    }


    void createUser(String userId, String password) throws Exception {
        storage.createUser(userId, password);
        storage.setBalance(userId, defaultBalance);
    }

    String getUserId(String token) throws StatusException {
        if (Strings.isNullOrEmpty(token)) {
            throw new StatusException(Status.UNAUTHENTICATED.withDescription("no auth token provided"));
        }

        String userId = storage.getUserIdFromToken(token);
        if (Strings.isNullOrEmpty(userId)) {
            throw new StatusException(Status.UNAUTHENTICATED.withDescription("invalid auth token provided"));
        }

        return userId;
    }

    private void validatePrice(double price) throws Exception {
        if (price <= 0) {
            throw new Exception("price should be positive");
        }
    }

    private SellInfo createSellInfo(double price, VaccineInfo info) {
        String id = UUID.randomUUID().toString();
        storage.saveSell(id, info, price);
        return SellInfo.newBuilder().setId(id).setPrice(price).build();
    }

    Vaccine createVaccine(String userId, CreateVaccineRequest request) throws Exception {
        if (Strings.isNullOrEmpty(request.getRnaInfo())) {
            throw new Exception("rna info empty");
        }

        if (Strings.isNullOrEmpty(request.getName())) {
            throw new Exception("vaccine name empty");
        }

        validatePrice(request.getPrivatePrice());

        if (request.hasPublicPrice()) {
            validatePrice(request.getPublicPrice().getPrice());
        }

        if (storage.getUserPrivateStock(userId) != null) {
            throw new StatusException(Status.ALREADY_EXISTS.withDescription("vaccine already exists for this user"));
        }

        VaccineInfo info = VaccineInfo
                .newBuilder()
                .setRnaInfo(request.getRnaInfo())
                .setName(request.getName())
                .setSellerId(userId)
                .build();

        Vaccine.Builder builder = Vaccine.newBuilder().setInfo(info);

        SellInfo privateInfo = createSellInfo(request.getPrivatePrice(), info);
        storage.saveUserPrivateStock(userId, privateInfo.getId());

        builder.setPrivate(privateInfo);

        if (!request.hasPublicPrice()) {
            return builder.build();
        }

        SellInfo publicInfo = createSellInfo(request.getPublicPrice().getPrice(), info);
        storage.saveUserPublicStock(userId, publicInfo.getId());

        storage.addToPublicList(ListVaccineInfo
                .newBuilder()
                .setName(request.getName())
                .setStockId(publicInfo.getId())
                .build()
        );

        return builder.setPublic(publicInfo).build();
    }

    VaccineInfo buy(String userId, String stockId) throws Exception {
        Lock sellLock = locks.get(stockId);
        sellLock.lock();


        try {
            VaccineInfo info = storage.getVaccineInfo(stockId);
            String sellerId = info.getSellerId();

            if (userId.equals(sellerId)) {
                throw new Exception("you can't buy your own vaccine");
            }

            String minUserId = sellerId;
            String maxUserId = userId;
            if (minUserId.compareTo(maxUserId) > 0) {
                String tmp = minUserId;
                minUserId = maxUserId;
                maxUserId = tmp;
            }

            Lock minLock = locks.get(minUserId);
            Lock maxLock = locks.get(maxUserId);
            minLock.lock();
            maxLock.lock();

            try {
                double userBalance = storage.getBalance(userId);
                double price = storage.getPrice(stockId);

                if (userBalance < price) {
                    throw new Exception("not enough money to buy");
                }

                userBalance -= price;
                storage.setBalance(userId, userBalance);
                storage.setBalance(sellerId, storage.getBalance(sellerId) + price);
                storage.savePrice(stockId, price * 2);

                return info;
            } finally {
                maxLock.unlock();
                minLock.unlock();
            }
        } finally {
            sellLock.unlock();
        }
    }

    double getBalance(String userId) {
        return storage.getBalance(userId);
    }

    double getPrice(String stockId) throws Exception {
        return storage.getPrice(stockId);
    }

    Vaccine getUserVaccine(String userId) throws Exception {
        String privateStockId = storage.getUserPrivateStock(userId);
        if (Strings.isNullOrEmpty(privateStockId)) {
            throw new StatusException(Status.NOT_FOUND.withDescription("sell info not found for user"));
        }

        VaccineInfo info = storage.getVaccineInfo(privateStockId);
        double privatePrice = storage.getPrice(privateStockId);

        Vaccine.Builder builder = Vaccine
                .newBuilder()
                .setInfo(info)
                .setPrivate(SellInfo.newBuilder().setPrice(privatePrice).setId(privateStockId));

        String publicStockId = storage.getUserPublicStock(userId);
        if (publicStockId == null) {
            return builder.build();
        }

        double publicPrice = storage.getPrice(publicStockId);

        return builder.setPublic(SellInfo.newBuilder().setId(publicStockId).setPrice(publicPrice)).build();
    }

    List<ListVaccineInfo> getLatestInfos() {
        return storage.getPublicInfos(fetchLastN);
    }
}
