package exchange;

import java.security.SecureRandom;
import java.util.Random;

public class RandomHelper {
    static char[] Alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789".toCharArray();

    static Random rand = new SecureRandom();

    public static String getString(int length) {
        char[] gen = new char[length];

        for (int i = 0 ; i < length; i++) {
            gen[i] = Alphabet[rand.nextInt(Alphabet.length)];
        }

        return new String(gen);
    }
}
