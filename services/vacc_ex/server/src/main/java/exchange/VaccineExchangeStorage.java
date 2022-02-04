package exchange;

import com.google.common.base.Strings;
import exchange.proto.Exchange;
import redis.clients.jedis.Jedis;
import redis.clients.jedis.JedisPool;
import redis.clients.jedis.params.SetParams;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.logging.Logger;

public class VaccineExchangeStorage {
    private static final Logger logger = Logger.getLogger(VaccineExchangeStorage.class.getName());

    private static final String usersSetPrefix = "user_";
    private static final String tokensSet = "tokens_";
    private static final String sellInfosSet = "stock_";
    private static final String latestStocks = "latest_stocks";

    private final JedisPool jedisPool;


    VaccineExchangeStorage(String redisHost, int redisPort) {
        jedisPool = new JedisPool(redisHost, redisPort);
    }

    void createUser(String userId, String password) throws Exception {
        String key = usersSetPrefix + userId;
        try (Jedis jedis = jedisPool.getResource()) {
            if (jedis.hexists(key, "password")) {
                throw new Exception("user with this id already exists");
            }

            jedis.hset(key, "password", password);
        }
    }

    String findUserPassword(String userId) {
        String key = usersSetPrefix + userId;
        try (Jedis jedis = jedisPool.getResource()) {
            String password = jedis.hget(key, "password");

            if (Strings.isNullOrEmpty(password)) {
                return null;
            }

            return password;
        }
    }

    void setBalance(String userId, double balance) {
        try (Jedis jedis = jedisPool.getResource()) {
            jedis.hset(usersSetPrefix + userId, "balance", Double.toString(balance));
        }
    }

    double getBalance(String userId) {
        try (Jedis jedis = jedisPool.getResource()) {
            return Double.parseDouble(jedis.hget(usersSetPrefix + userId, "balance"));
        }
    }

    void saveToken(String userId, String token, long expireSeconds) {
        try (Jedis jedis = jedisPool.getResource()) {
            jedis.set(tokensSet + token, userId, SetParams.setParams().ex(expireSeconds));
        }
    }

    String getUserIdFromToken(String token) {
        try (Jedis jedis = jedisPool.getResource()) {
            return jedis.get(tokensSet + token);
        }
    }

    void saveSell(String stockId, Exchange.VaccineInfo info, double price) {
        try (Jedis jedis = jedisPool.getResource()) {
            savePrice(jedis, stockId, price);
            jedis.hset((sellInfosSet + stockId).getBytes(), "info".getBytes(), info.toByteArray());
        }
    }

    void savePrice(Jedis jedis, String stockId, double price) {
        jedis.hset(sellInfosSet + stockId, "price", Double.toString(price));
    }

    void savePrice(String stockId, double price) {
        try (Jedis jedis = jedisPool.getResource()) {
            savePrice(jedis, stockId, price);
        }
    }

    public Exchange.VaccineInfo getVaccineInfo(String stockId) throws Exception {
        try (Jedis jedis = jedisPool.getResource()) {
            String data = jedis.hget(sellInfosSet + stockId, "info");
            if (data == null) {
                throw new Exception("vaccine info not found by id " + stockId);
            }
            return Exchange.VaccineInfo.parseFrom(data.getBytes());
        }
    }


    public double getPrice(String stockId) throws Exception {
        try (Jedis jedis = jedisPool.getResource()) {
            String doublePrice = jedis.hget(sellInfosSet + stockId, "price");
            if (doublePrice == null) {
                throw new Exception("stock price not found by id " + stockId);
            }
            return Double.parseDouble(doublePrice);
        }
    }

    String getUserPublicStock(String userId) {
        try (Jedis jedis = jedisPool.getResource()) {
            return jedis.hget(usersSetPrefix + userId, "public_stock_id");
        }
    }

    String getUserPrivateStock(String userId) {
        try (Jedis jedis = jedisPool.getResource()) {
            return jedis.hget(usersSetPrefix + userId, "private_stock_id");
        }
    }

    void saveUserPrivateStock(String userId, String stockId) {
        try (Jedis jedis = jedisPool.getResource()) {
            jedis.hset(usersSetPrefix + userId, "private_stock_id", stockId);
        }
    }

    void saveUserPublicStock(String userId, String stockId) {
        try (Jedis jedis = jedisPool.getResource()) {
            jedis.hset(usersSetPrefix + userId, "public_stock_id", stockId);
        }
    }

    void addToPublicList(Exchange.ListVaccineInfo info) {
        try (Jedis jedis = jedisPool.getResource()) {
            jedis.rpush(latestStocks.getBytes(), info.toByteArray());
        }
    }


    List<Exchange.ListVaccineInfo> getPublicInfos(long limit) {
        try (Jedis jedis = jedisPool.getResource()) {
            List<byte[]> latestBytes = jedis.lrange(latestStocks.getBytes(), -limit - 1, -1);
            Collections.reverse(latestBytes);
            List<Exchange.ListVaccineInfo> infos = new ArrayList<>();
            for (byte[] b: latestBytes) {
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
