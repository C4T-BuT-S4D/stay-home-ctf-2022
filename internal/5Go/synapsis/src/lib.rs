use protobuf::Message;

use crate::crypto::KeyPair;
use crate::neurotransmitter::{AsymmetricKey, SerializedStuff};

mod crypto;
mod neurotransmitter;

fn serialize_data(data: &[u8]) -> Option<Vec<u8>> {
    let mut stuff = SerializedStuff::new();
    stuff.set_content(data.to_vec());
    stuff.write_to_bytes().ok()
}

fn deserialize_data(data: &[u8]) -> Option<Vec<u8>> {
    Some(
        SerializedStuff::parse_from_bytes(data)
            .ok()?
            .get_content()
            .to_vec()
    )
}

pub fn generate_key() -> Vec<u8> {
    let key = crypto::KeyPair::new();
    key.to_proto().write_to_bytes().unwrap()
}

pub fn generate_shared(raw_pair: &[u8], raw_pubkey: &[u8]) -> Option<Vec<u8>> {
    let mut shared = AsymmetricKey::parse_from_bytes(raw_pair).ok()?;
    let pubkey_stuff = SerializedStuff::parse_from_bytes(raw_pubkey).ok()?;
    shared.set_public_key(pubkey_stuff);
    Some(serialize_data(KeyPair::from_proto(&shared)?.get_shared().as_slice())?)
}

pub fn encrypt(raw_key: &[u8], raw_message: &[u8]) -> Option<Vec<u8>> {
    let key = deserialize_data(&raw_key)?;
    let message = deserialize_data(&raw_message)?;
    let raw_enc = crypto::encrypt_message(key.as_slice(), message.as_slice());
    serialize_data(&raw_enc)
}

pub fn decrypt(raw_key: &[u8], raw_encrypted: &[u8]) -> Option<Vec<u8>> {
    let key = deserialize_data(&raw_key)?;
    let encrypted = deserialize_data(&raw_encrypted)?;
    let raw_mess = crypto::decrypt_message(key.as_slice(), encrypted.as_slice())?;
    serialize_data(&raw_mess)
}

#[cfg(test)]
mod tests {
    use crate::neurotransmitter::AsymmetricKey;

    use super::*;

    #[test]
    fn test_encryption_e2e() {
        // Clients 1 and 2 generate two keys.
        let key_dump_1 = generate_key();
        let key_dump_2 = generate_key();

        // They decode asymmetric keys on their side (go/python/etc)
        let key1 = AsymmetricKey::parse_from_bytes(key_dump_1.as_slice()).unwrap();
        let key2 = AsymmetricKey::parse_from_bytes(key_dump_2.as_slice()).unwrap();

        // They share public keys (as SerializedStuff) and generate shared (session) keys
        let shared1 = generate_shared(
            key_dump_1.as_slice(),
            key2.get_public_key().write_to_bytes().unwrap().as_slice(),
        ).unwrap();
        let shared2 = generate_shared(
            key_dump_2.as_slice(),
            key1.get_public_key().write_to_bytes().unwrap().as_slice(),
        ).unwrap();

        assert_eq!(shared1, shared2, "Shared keys differ");

        // And finally they encrypt/decrypt (notice the different keys).
        let message = serialize_data("memkek".as_bytes()).unwrap();
        let encrypted = encrypt(shared1.as_slice(), message.as_slice()).unwrap();
        let decrypted = decrypt(shared2.as_slice(), encrypted.as_slice()).unwrap();

        assert_eq!(message, decrypted, "Cryptography is not correct");
    }
}

#[cfg(feature = "ffi")]
mod ffi {
    extern crate libc;

    use crate::*;

    #[repr(C)]
    pub struct Buffer {
        len: usize,
        data: *mut u8,
        error: bool,
    }

    unsafe fn decode_buf(buf: &Buffer) -> &mut [u8] {
        std::slice::from_raw_parts_mut(buf.data, buf.len)
    }

    unsafe fn safe_empty_buf(error: bool) -> Buffer {
        let data: *mut u8 = std::slice::from_raw_parts_mut(std::ptr::null_mut(), 0).as_mut_ptr();
        std::mem::forget(data);
        Buffer { len: 0, data, error }
    }

    unsafe fn encode_buf(content: &[u8]) -> Buffer {
        if content.len() == 0 {
            return safe_empty_buf(false)
        }
        let mut buf = content.to_vec().into_boxed_slice();
        let data = buf.as_mut_ptr();
        let len = buf.len();
        std::mem::forget(buf);
        Buffer { len, data, error: false }
    }

    unsafe fn error_buf() -> Buffer {
        safe_empty_buf(true)
    }

    #[allow(dead_code)]
    #[no_mangle]
    unsafe extern "C" fn free_buf(buf: Buffer) {
        if buf.len != 0 {
            let s = decode_buf(&buf);
            let s = s.as_mut_ptr();
            Box::from_raw(s);
        }
    }

    #[allow(dead_code)]
    #[no_mangle]
    unsafe extern "C" fn generate_key_ffi() -> Buffer {
        encode_buf(generate_key().as_slice())
    }

    #[allow(dead_code)]
    #[no_mangle]
    unsafe extern "C" fn generate_shared_ffi(pair_buf: Buffer, pubkey_buf: Buffer) -> Buffer {
        let pair = decode_buf(&pair_buf);
        let pubkey = decode_buf(&pubkey_buf);
        match generate_shared(pair, pubkey) {
            Some(shared) => encode_buf(shared.as_slice()),
            None => error_buf(),
        }
    }

    #[allow(dead_code)]
    #[no_mangle]
    unsafe extern "C" fn encrypt_ffi(key_buf: Buffer, message_buf: Buffer) -> Buffer {
        let key = decode_buf(&key_buf);
        let msg = decode_buf(&message_buf);
        match encrypt(&key, &msg) {
            Some(enc) => encode_buf(enc.as_slice()),
            None => error_buf(),
        }
    }

    #[allow(dead_code)]
    #[no_mangle]
    unsafe extern "C" fn decrypt_ffi(key_buf: Buffer, encrypted_buf: Buffer) -> Buffer {
        let key = decode_buf(&key_buf);
        let enc = decode_buf(&encrypted_buf);
        match decrypt(&key, &enc) {
            Some(msg) => encode_buf(msg.as_slice()),
            None => error_buf(),
        }
    }
}

#[cfg(feature = "pyo3")]
mod ozone {
    use pyo3::prelude::*;
    use pyo3::types::PyBytes;

    use crate::*;

    #[pyfunction]
    #[pyo3(name = "generate_key")]
    fn generate_key_o3(py: Python) -> PyObject {
        PyBytes::new(py, generate_key().as_slice()).into()
    }

    #[pyfunction]
    #[pyo3(name = "generate_shared")]
    fn generate_shared_o3(py: Python, pair: &[u8], pubkey: &[u8]) -> Option<PyObject> {
        Some(PyBytes::new(py, generate_shared(pair, pubkey)?.as_slice()).into())
    }

    #[pyfunction]
    #[pyo3(name = "encrypt")]
    fn encrypt_o3(py: Python, key: &[u8], message: &[u8]) -> Option<PyObject> {
        Some(PyBytes::new(py, encrypt(key, message)?.as_slice()).into())
    }

    #[pyfunction]
    #[pyo3(name = "decrypt")]
    fn decrypt_o3(py: Python, key: &[u8], encrypted: &[u8]) -> Option<PyObject> {
        Some(PyBytes::new(py, decrypt(key, encrypted)?.as_slice()).into())
    }

    #[pymodule]
    #[allow(unused_variables)]
    fn synapsis(py: Python, m: &PyModule) -> PyResult<()> {
        m.add_function(wrap_pyfunction!(generate_key_o3, m)?)?;
        m.add_function(wrap_pyfunction!(generate_shared_o3, m)?)?;
        m.add_function(wrap_pyfunction!(encrypt_o3, m)?)?;
        m.add_function(wrap_pyfunction!(decrypt_o3, m)?)?;
        Ok(())
    }
}

