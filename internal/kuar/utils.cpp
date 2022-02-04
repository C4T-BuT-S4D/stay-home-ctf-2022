#include "utils.hpp"

uint8_t* utils::ReadFile(const char* filename, int32_t* outSize)
{
    std::ifstream file(filename, std::ios::binary);
    file.unsetf(std::ios::skipws);
    std::streampos fileSize;

    file.seekg(0, std::ios::end);
    fileSize = file.tellg();
    file.seekg(0, std::ios::beg);


    uint8_t* data = new uint8_t[fileSize];
    *outSize = fileSize;

    file.read((char*)data, fileSize);
    
    return data;
};

uint32_t utils::count(uint8_t* pObj, char sym) {
    uint32_t cnt = 0;

    for (uint32_t i = 0; pObj[i] != '\0'; i++) {
        if ((char)pObj[i] == sym) {
            cnt++;
        }    
    }
    return cnt;
};

std::ifstream::pos_type utils::filesize(const char* filename)
{
    std::ifstream in(filename, std::ifstream::ate | std::ifstream::binary);
    return in.tellg(); 
}