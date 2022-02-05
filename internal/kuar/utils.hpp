#pragma once

#include <vector>
#include <fstream>
#include <iterator>
#include <string>

#include <sys/stat.h>


namespace utils {
    uint8_t* ReadFile(const char* filename, int32_t* outSize);
    uint32_t count(uint8_t* pObj, char sym);
    std::ifstream::pos_type filesize(const char* filename);
};