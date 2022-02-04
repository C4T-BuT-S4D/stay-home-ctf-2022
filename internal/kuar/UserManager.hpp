#pragma once
#include <cstdint>
#include <string>
#include <filesystem>

#include "Protocol.hpp"
#include "utils.hpp"
#include "qrcodegen.hpp"


constexpr char USER_MENU[] = "1. View Profile\n2. Update Profile\n3. Get QR-code\n4. Exit\n> ";
constexpr char DIR_PATH[] = "./users/";
constexpr char PASSWORD_FILE[] = "shadow.dat";
constexpr char PROFILE_FILENAME[] = "profile.dat";
constexpr char QR_CODE_FILENAME[] = "qrcode.dat";
constexpr char UPDATE_PROFILE_MSG[] = "[?] Send new profile info in format <Name-Surname>|<Birth-date>|<City>|<Vaccination-date>|<Vaccine-name>|<Additional-info>\n";
constexpr char UPDATE_PROFILE_FORMAT_ERROR_MSG[] = "[-] Format error!\n";
constexpr char NO_PROFILE_FILE[] = "[-] Profile not exist!\n";
constexpr char PROFILE_FORMAT_ERR[] = "[-] Profile format error!\n[!] Please update profile!\n";
constexpr char VIEW_PROFILE_FMTSTR[] = "Name: %s\nBirth-date: %s\nCity: %s\nVaccination-date: %s\nVaccine-name: %s\nInfo: %s\n";

constexpr uint32_t USERNAME_MAX_SIZE = 32;
constexpr uint32_t PASSWORD_MAX_SIZE = 32;
constexpr uint32_t OPTION_PACKET_SIZE = 16;
constexpr uint32_t UPDATE_PROFILE_PACKET_SIZE = 512;

class UserManager {
    private:
        Proto* m_session;
        char* m_Username;
    public:
        UserManager(Proto* pSession);
        ~UserManager();
        // basic menu
        bool Login();
        bool Register();

        // user menu
        int32_t UserMenu(void);
        int32_t ViewProfile(void);
        int32_t UpdateProfile(void);

        std::vector<std::string> ReadProfile(void);
        int32_t GetQR(void);

        bool PathIsExist(char* path);
        void Trim(char* str);
};


std::string QrToString(const qrcodegen::QrCode &qr);