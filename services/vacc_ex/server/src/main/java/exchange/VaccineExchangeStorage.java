package exchange;

import com.google.common.base.Strings;
import exchange.proto.Exchange;
import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPool;
import redis.clients.jedis.JedisPoolConfig;
import redis.clients.jedis.params.SetParams;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.logging.Logger;

public class VaccineExchangeStorage {
    public static class Context implements AutoCloseable {
        private final Jedis jedis;

        public Context(Jedis jed) {
            jedis = jed;
        }

        @Override
        public void close() {
            jedis.close();
        }
    }


    private static final Logger logger = Logger.getLogger(VaccineExchangeStorage.class.getName());

    private static final String usersSetPrefix = "user_";
    private static final String tokensSet = "tokens_";
    private static final String sellInfosSet = "stock_";
    private static final String latestStocks = "latest_stocks";

    private final JedisPool jedisPool;


    VaccineExchangeStorage(String redisHost, int redisPort) {
        JedisPoolConfig config = new JedisPoolConfig();
        config.setMaxTotal(100);
        jedisPool = new JedisPool(config, redisHost, redisPort);

    }

    Context newContext() {
        return new Context(jedisPool.getResource());
    }

    void createUser(Context ctx, String userId, String password) throws Exception {
        String key = usersSetPrefix + userId;

        if (ctx.jedis.hexists(key, "password")) {
            throw new Exception("user with this id already exists");
        }

        ctx.jedis.hset(key, "password", password);
    }

    String findUserPassword(Context ctx, String userId) {
        String key = usersSetPrefix + userId;
        String password = ctx.jedis.hget(key, "password");

        if (Strings.isNullOrEmpty(password)) {
            return null;
        }

        return password;
    }

    void setBalance(Context ctx, String userId, double balance) {
        ctx.jedis.hset(usersSetPrefix + userId, "balance", Double.toString(balance));
    }

    double getBalance(Context ctx, String userId) {
        return Double.parseDouble(ctx.jedis.hget(usersSetPrefix + userId, "balance"));
    }

    double getBalance(String userId) {
        try (Context ctx = newContext()) {
            return getBalance(ctx, userId);
        }
    }

    void saveToken(Context ctx, String userId, String token, long expireSeconds) {
        ctx.jedis.set(tokensSet + token, userId, SetParams.setParams().ex(expireSeconds));
    }

    String getUserIdFromToken(String token) {
        try (Context ctx = newContext()) {
            return ctx.jedis.get(tokensSet + token);
        }
    }

    void saveSell(Context ctx, String stockId, Exchange.VaccineInfo info, double price) {
        savePrice(ctx, stockId, price);
        ctx.jedis.hset((sellInfosSet + stockId).getBytes(), "info".getBytes(), info.toByteArray());
    }

    void savePrice(Context ctx, String stockId, double price) {
        ctx.jedis.hset(sellInfosSet + stockId, "price", Double.toString(price));
    }

    public double getPrice(Context ctx, String stockId) throws Exception {
        String doublePrice = ctx.jedis.hget(sellInfosSet + stockId, "price");
        if (doublePrice == null) {
            throw new Exception("stock price not found by id " + stockId);
        }
        return Double.parseDouble(doublePrice);
    }

    public double getPrice(String stockId) throws Exception {
        try (Context ctx = newContext()) {
            return getPrice(ctx, stockId);
        }
    }

    public Exchange.VaccineInfo getVaccineInfo(Context ctx, String stockId) throws Exception {
        String data = ctx.jedis.hget(sellInfosSet + stockId, "info");
        if (data == null) {
            throw new Exception("vaccine info not found by id " + stockId);
        }
        return Exchange.VaccineInfo.parseFrom(data.getBytes());
    }

    String getUserPublicStock(String userId) {
        try (Context ctx = newContext()) {
            return ctx.jedis.hget(usersSetPrefix + userId, "public_stock_id");
        }
    }

    String getUserPrivateStock(Context ctx, String userId) {
        return ctx.jedis.hget(usersSetPrefix + userId, "private_stock_id");
    }

    void saveUserPrivateStock(Context ctx, String userId, String stockId) {
        ctx.jedis.hset(usersSetPrefix + userId, "private_stock_id", stockId);
    }

    void saveUserPublicStock(Context ctx, String userId, String stockId) {
        ctx.jedis.hset(usersSetPrefix + userId, "public_stock_id", stockId);
    }

    void addToPublicList(Context ctx, Exchange.ListVaccineInfo info) {
        ctx.jedis.rpush(latestStocks.getBytes(), info.toByteArray());
    }


    List<Exchange.ListVaccineInfo> getPublicInfos(long limit) {
        try (Context ctx = newContext()) {
            List<byte[]> latestBytes = ctx.jedis.lrange(latestStocks.getBytes(), -limit - 1, -1);
            Collections.reverse(latestBytes);
            List<Exchange.ListVaccineInfo> infos = new ArrayList<>();
            for (byte[] b : latestBytes) {
                try {
                    infos.add(Exchange.ListVaccineInfo.parseFrom(b));
                } catch (Exception e) {
                    logger.info("failed to decode list record");
                }
            }
            return infos;
        }
    }
}
