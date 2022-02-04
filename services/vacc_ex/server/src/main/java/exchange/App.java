package exchange;

public class App {
    public static int portFromEnv(String key, int def) throws Exception {
        String portString = System.getenv().getOrDefault(key, Integer.toString(def));
        return Integer.parseInt(portString);
    }

    public static void main(String[] args) throws Exception {
        VaccineExchangeServer server = new VaccineExchangeServer(
                portFromEnv("APP_PORT", 8980),
                new VaccineExchangeRpc(
                        new VaccineExchangeService(
                                new VaccineExchangeStorage(
                                        System.getenv().getOrDefault("REDIS_HOST", "localhost"),
                                        portFromEnv("REDIS_PORT", 6379)
                                )
                        )
                ));
        server.start();
        server.blockUntilShutdown();
    }
}
