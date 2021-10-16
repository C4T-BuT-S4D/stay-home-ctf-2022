use std::fmt::Debug;

use crate::neurotransmitter::AsymmetricKey;
use aes::cipher::generic_array::GenericArray;
use aes::{Block, BlockDecrypt, BlockEncrypt, NewBlockCipher};
use rand_core::OsRng;
use x25519_dalek::{PublicKey, StaticSecret};

pub struct KeyPair {
    pub secret: StaticSecret,
    pub pubkey: PublicKey,
}

impl KeyPair {
    pub fn new() -> KeyPair {
        let secret = StaticSecret::new(OsRng);
        let pubkey = PublicKey::from(&secret);
        KeyPair { secret, pubkey }
    }

    pub fn from_proto(proto: &AsymmetricKey) -> Option<KeyPair> {
        let secret = utils::secret_from_proto(proto.get_secret())?;
        let pubkey = utils::pubkey_from_proto(proto.get_public_key())?;
        Some(KeyPair { secret, pubkey })
    }

    pub fn to_proto(&self) -> AsymmetricKey {
        let mut res = AsymmetricKey::new();
        res.set_secret(utils::secret_to_proto(&self.secret));
        res.set_public_key(utils::pubkey_to_proto(&self.pubkey));
        res
    }

    pub fn get_shared(&self) -> Vec<u8> {
        self.secret
            .diffie_hellman(&self.pubkey)
            .to_bytes()
            .to_vec()
    }
}

impl PartialEq for KeyPair {
    fn eq(&self, other: &Self) -> bool {
        return self.secret.to_bytes() == other.secret.to_bytes() && self.pubkey.to_bytes() == other.pubkey.to_bytes();
    }
}

impl Debug for KeyPair {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("KeyPair")
            .field("secret", &self.secret.to_bytes())
            .field("pubkey", &self.pubkey.to_bytes())
            .finish()
    }
}

pub fn encrypt_message(key: &[u8], message: &[u8]) -> Vec<u8> {
    let cipher = aes::Aes256::new(GenericArray::from_slice(key));
    let padded = utils::pad_message(message, 16);
    let mut blocks: Vec<Block> = padded
        .chunks(16)
        .map(|x| *Block::from_slice(x))
        .collect();

    cipher.encrypt_blocks(&mut blocks);
    let ret = blocks.concat();
    ret
}

pub fn decrypt_message(key: &[u8], encrypted: &[u8]) -> Option<Vec<u8>> {
    if encrypted.len() % 16 != 0 {
        return None;
    }
    let cipher = aes::Aes256::new(GenericArray::from_slice(key));
    let mut blocks: Vec<Block> = encrypted
        .chunks(16)
        .map(|x| *Block::from_slice(x))
        .collect();

    cipher.decrypt_blocks(&mut blocks);
    let full = blocks.concat();
    let ret = Some(utils::unpad_message(&full)?.to_vec());
    ret
}

mod utils {
    use crate::neurotransmitter::SerializedStuff;
    use std::convert::TryFrom;
    use std::io::{repeat, Read};
    use x25519_dalek::{PublicKey, StaticSecret};

    pub fn bytes_to_stuff(b: &[u8]) -> SerializedStuff {
        let mut stuff = SerializedStuff::new();
        stuff.set_content(b.to_vec());
        stuff
    }

    pub fn secret_from_proto(stuff: &SerializedStuff) -> Option<StaticSecret> {
        Some(StaticSecret::from(<[u8; 32]>::try_from(stuff.content.as_slice()).ok()?))
    }

    pub fn secret_to_proto(secret: &StaticSecret) -> SerializedStuff {
        bytes_to_stuff(&secret.to_bytes())
    }

    pub fn pubkey_to_proto(pk: &PublicKey) -> SerializedStuff {
        bytes_to_stuff(&pk.to_bytes())
    }

    pub fn pubkey_from_proto(stuff: &SerializedStuff) -> Option<PublicKey> {
        Some(PublicKey::from(<[u8; 32]>::try_from(stuff.content.as_slice()).ok()?))
    }

    pub fn pad_message(message: &[u8], size: usize) -> Vec<u8> {
        let pc = size - message.len() % size;
        let padding: Vec<u8> = repeat(pc as u8)
            .take(pc as u64)
            .bytes()
            .map(|x| x.unwrap())
            .collect();

        let mut result = message.to_vec();
        result.extend(padding);
        result
    }

    pub fn unpad_message(message: &[u8]) -> Option<&[u8]> {
        let pc = *message.last()? as usize;
        Some(&message[0..message.len() - pc])
    }

    #[cfg(test)]
    mod tests {
        use rand_core::OsRng;
        use x25519_dalek::{StaticSecret, PublicKey};

        use super::*;

        #[test]
        fn test_padding() {
            let message = "keklol".as_bytes();
            let padded = pad_message(message, 16);
            assert_eq!(padded.len(), 16, "Invalid padding");
            let unpadded = unpad_message(&padded).unwrap();
            assert_eq!(unpadded, message, "Padding is not reversible");
        }

        #[test]
        fn test_secret_serialization() {
            let secret = StaticSecret::new(OsRng);
            let serialized = secret_to_proto(&secret);
            let deserialized = secret_from_proto(&serialized).unwrap();
            assert_eq!(secret.to_bytes(), deserialized.to_bytes(), "Secret serialization is not reversible");
        }

        #[test]
        fn test_pubkey_serialization() {
            let secret = StaticSecret::new(OsRng);
            let pk = PublicKey::from(&secret);
            let serialized = pubkey_to_proto(&pk);
            let deserialized = pubkey_from_proto(&serialized).unwrap();
            assert_eq!(pk.to_bytes(), deserialized.to_bytes(), "Public key serialization is not reversible");
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_keypair_serialization() {
        let pair = KeyPair::new();
        let serialized = pair.to_proto();
        let deserialized = KeyPair::from_proto(&serialized).unwrap();
        assert_eq!(pair, deserialized, "KeyPair serialization is not reversible");
    }

    #[test]
    fn test_encryption() {
        let alice_key = KeyPair::new();
        let bob_key = KeyPair::new();

        let alice_pair = KeyPair { secret: alice_key.secret, pubkey: bob_key.pubkey };
        let bob_pair = KeyPair { secret: bob_key.secret, pubkey: alice_key.pubkey };

        let alice_shared = alice_pair.get_shared();
        let bob_shared = bob_pair.get_shared();

        assert_eq!(alice_shared, bob_shared, "Generated shared keys are not equal");

        let message = "memkek".as_bytes();
        let encrypted = encrypt_message(&alice_shared, &message);
        let decrypted = decrypt_message(&bob_shared, &encrypted).unwrap();
        assert_eq!(message, decrypted);
    }
}
