struct Buffer {
    size_t len;
    char *data;
    char error;
};

struct Buffer generate_key_ffi();

struct Buffer generate_shared_ffi(struct Buffer pair, struct Buffer pubkey);

struct Buffer encrypt_ffi(struct Buffer key, struct Buffer message);

struct Buffer decrypt_ffi(struct Buffer key, struct Buffer encrypted);

void free_buf(struct Buffer);
