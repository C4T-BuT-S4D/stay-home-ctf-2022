#include "Protocol.hpp"


Proto::Proto() {
    setvbuf(stdin, 0, 2, 0);
    setvbuf(stdout, 0, 2, 0);
    setvbuf(stderr, 0, 2, 0);

    // read key init value
    uint8_t* buf = new uint8_t[INIT_PACKET_SIZE];
    int32_t len = read(0, buf, INIT_PACKET_SIZE);

    if (len <= 0) {
        exit(KEY_INIT_ERROR);
    }

    if (len != 64) {
        exit(KEY_INIT_SIZE_ERROR);
    }

    GenerateKey(buf, INIT_PACKET_SIZE);
};

Proto::~Proto() {
    if (m_buf != nullptr) {
        delete[] m_buf;
    }
    
    if (m_key != nullptr) {
        delete[] m_key;
    }

    if (m_cipherCtx != nullptr) {
        delete m_cipherCtx;
    }
};

int32_t Proto::Recv(uint8_t* packet, uint32_t size) {
    try {
        m_packetSize = read(0, packet, size);

        if (m_packetSize <= 0) {
            throw std::runtime_error(std::strerror(errno));
        }

        if (std::ferror(stdin) && !std::feof(stdin)) {
            throw std::runtime_error(std::strerror(errno));
        }
    }
    catch (std::exception const& e) {
        std::cerr << e.what() << '\n';
        exit(RECV_ERROR);
    }
    
    m_buf = DecryptPacket(packet, &m_packetSize);
    std::memcpy(packet, m_buf, m_packetSize);
    delete[] m_buf;

    return m_packetSize;
};
    
int32_t Proto::Send(uint8_t* packet, uint32_t size) {
    if (size <= 0) {
        return 0;
    }

    m_buf = EncryptPacket(packet, &size);

    try {
        m_packetSize = write(1, m_buf, size);
        delete[] m_buf;
        usleep(10000);

        if (m_packetSize <= 0) {
            throw std::runtime_error(std::strerror(errno));
        }

        if (std::ferror(stdout) && !std::feof(stdout)) {
            throw std::runtime_error(std::strerror(errno));
        }
    }
    catch (std::exception const& e) {
        std::cerr << e.what() << '\n';
        exit(SEND_ERROR);
    }

    return m_packetSize;
};

// s-table based algo
void Proto::GenerateKey(uint8_t* data, uint32_t size) {
    std::vector<uint8_t> vec1;
    std::vector<uint8_t> vec2;
    
    for (uint32_t i = 0; i < size; i += 2) {
        vec1.push_back(stable[data[i]]);
        vec2.push_back(stable[data[i + 1]]);
    }

    m_keySize = vec1.size();
    m_key = new uint8_t[m_keySize];

    for (uint32_t i = 0; i < vec1.size(); i++) {
        m_key[i] = vec1[i] ^ vec2[i];
    }
    
    CreateCipherCtx();
};

void Proto::CreateCipherCtx(void) {
    if (m_keySize != 32) {
        m_keySize = 32;
    }

    m_cipherCtx = new AES(m_keySize * 8);
};

uint8_t* Proto::EncryptPacket(uint8_t* packet, uint32_t* size) {
    int8_t padByte = 16 - (*size % 16);
    uint8_t* tmp = new uint8_t[*size + padByte];

    std::memset(tmp, padByte, *size + padByte);
    std::memcpy(tmp, packet, *size);
    
    *size += padByte;
    packet = tmp;
    
    uint32_t outSize;
    uint8_t* encPacket = m_cipherCtx->EncryptECB(packet, *size, m_key, outSize);
    delete[] packet;
    return encPacket;
};

uint8_t* Proto::DecryptPacket(uint8_t* packet, uint32_t* size) {
    uint8_t* decPacket = m_cipherCtx->DecryptECB(packet, *size, m_key);
    int8_t padByte = decPacket[*size - 1];
 
    for (uint32_t i = *size - 1; i > (*size - padByte); i--) {
        if (decPacket[i] != padByte) {
            Send((uint8_t*)"[-] Incorrect padding!", sizeof("[-] Incorrect padding!"));
            exit(0);
        }
    }

    *size -= padByte;
    uint8_t* tmp = new uint8_t[*size + 1];
    std::memset(tmp, 0, *size + 1);
    std::memcpy(tmp, decPacket, *size);
    delete[] decPacket;
    return tmp;
};