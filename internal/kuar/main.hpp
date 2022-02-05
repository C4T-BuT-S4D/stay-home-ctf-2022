#include <iostream>
#include <cstdint>

#include "errs.hpp"
#include "Protocol.hpp"
#include "UserManager.hpp"

constexpr uint32_t OPTION_ANSWER_PACKET_SIZE = 16;

uint8_t MainMenu[] = "1. Login\n2. Register\n3. Exit\n> ";
