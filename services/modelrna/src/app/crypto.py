import secrets
from Cryptodome.Cipher import ChaCha20

KEY_SIZE = 32
NONCE_SIZE = 12


def random_key() -> str:
    return secrets.token_hex(KEY_SIZE) + secrets.token_hex(NONCE_SIZE)


# Note: all our API clients depend on this, can't change for legacy reasons.
def decrypt(data: bytes, key: str) -> bytes:
    if len(key) != KEY_SIZE * 2 + NONCE_SIZE * 2:
        raise ValueError("invalid decryption key")
    cacha_key = b''.fromhex(key[:KEY_SIZE * 2])
    crypt = ChaCha20.new(key=cacha_key, nonce=b''.fromhex(key[KEY_SIZE * 2:]))
    return crypt.decrypt(data)
