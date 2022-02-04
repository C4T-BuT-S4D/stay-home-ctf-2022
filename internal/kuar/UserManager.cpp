#include "UserManager.hpp"


UserManager::UserManager(Proto* pSession) {
    m_session = pSession;
};

UserManager::~UserManager() {
    if (m_session != nullptr) {
        delete m_session;
    }

    if (m_Username != nullptr) {
        delete m_Username;
    }
};

bool UserManager::PathIsExist(char* path) {
  struct stat buffer;
  return stat(path, &buffer) == 0; 
};

bool UserManager::Login() {
    // send username msg
    m_session->Send((uint8_t*)"[?] Username: ", sizeof("[?] Username: "));
    
    // get user answer
    uint8_t* Username = new uint8_t[USERNAME_MAX_SIZE];
    std::memset(Username, 0, USERNAME_MAX_SIZE);
    int nbytes = m_session->Recv(Username, USERNAME_MAX_SIZE);
    Username[nbytes] = '\0';
    
    // create path to user dir
    uint32_t UserPathSize = USERNAME_MAX_SIZE + strlen(DIR_PATH) 
    + strlen(PASSWORD_FILE) + 16;
    char* UserPath = new char[UserPathSize];
    std::memset(UserPath, 0, UserPathSize);

    Trim((char*)Username);
    std::sprintf(UserPath, "%s%s/%s", DIR_PATH, Username, PASSWORD_FILE);

    // check if dir exist
    if (!PathIsExist(UserPath)) {
        m_session->Send((uint8_t*)"[-] No such user!", sizeof("[-] No such user!"));
        delete[] Username;
        delete[] UserPath;
        return false;
    }

    // send password msg
    m_session->Send((uint8_t*)"[?] Password: ", sizeof("[?] Password: "));
    
    // get password
    uint8_t* Password = new uint8_t[PASSWORD_MAX_SIZE];
    nbytes = 0;
    nbytes = m_session->Recv(Password, PASSWORD_MAX_SIZE);

    // read password from config file
    uint8_t* FileData;
    int32_t PasswordFileSize = 0;
    FileData = utils::ReadFile(UserPath, &PasswordFileSize);

    // check user password size and file password size
    if (PasswordFileSize != nbytes) {
        m_session->Send((uint8_t*)"[-] Incorrect password!", sizeof("[-] Incorrect password!"));
        delete[] UserPath;
        delete[] Username;
        return false;
    }

    bool isLogined = true;

    for (uint32_t i = 0; i < PasswordFileSize; i++) {
        if (FileData[i] != Password[i]) {
            m_session->Send((uint8_t*)"[-] Incorrect password!", sizeof("[-] Incorrect password!"));
            delete[] UserPath;
            delete[] Username;
            return false;
        }
    }

    m_Username = (char*) Username;

    delete[] Password;
    delete[] UserPath;
    delete[] FileData;
    
    return isLogined;
};

bool UserManager::Register() {
    // send username msg
    m_session->Send((uint8_t*)"[?] Username: ", sizeof("[?] Username: "));
    
    // get user answer
    uint8_t* Username = new uint8_t[USERNAME_MAX_SIZE];
    std::memset(Username, 0, USERNAME_MAX_SIZE);
    uint32_t nbytes = m_session->Recv(Username, USERNAME_MAX_SIZE);
    Username[nbytes] = '\0';

    // create path to user dir
    uint32_t UserPathSize = USERNAME_MAX_SIZE + strlen(DIR_PATH) 
    + strlen(PASSWORD_FILE) + 16;

    char* UserPath = new char[UserPathSize];
    std::memset(UserPath, 0, UserPathSize);
    
    std::strcpy(UserPath, DIR_PATH);
    Trim((char*)Username);
    std::strncat(UserPath, (char*)Username, nbytes);
    
    // check if dir exist
    if (PathIsExist(UserPath)) {
        m_session->Send((uint8_t*)"[-] User exist!", sizeof("[-] User exist!"));
        return false;
    }

    // create dir
    std::filesystem::create_directory(UserPath);

    std::strcat(UserPath, "/");
    std::strcat(UserPath, PASSWORD_FILE);

    // send password msg
    m_session->Send((uint8_t*)"[?] Password: ", sizeof("[?] Password: "));
    
    // get password
    uint8_t* Password = new uint8_t[PASSWORD_MAX_SIZE];
    nbytes = m_session->Recv(Password, PASSWORD_MAX_SIZE);

    // write password to config file
    std::ofstream ConfigFile(UserPath);

    ConfigFile.write((const char*)Password, nbytes);
    ConfigFile.close();

    delete[] UserPath; 
    delete[] Password;

    m_Username = (char*) Username;
    return true;
};

int32_t UserManager::UserMenu(void) {
    while (true) {

        m_session->Send((uint8_t*)USER_MENU, sizeof(USER_MENU));

        uint8_t* optionPacket = new uint8_t[OPTION_PACKET_SIZE];
        m_session->Recv(optionPacket, OPTION_PACKET_SIZE);

        switch(optionPacket[0]) {
            case '1':
                ViewProfile();
                break;
            case '2':
                UpdateProfile();
                break;
            case '3':
                GetQR();
                break;
            case '4':
                return 0;
            default:
                return 0;
        }
        delete[] optionPacket;
    }
};

void UserManager::Trim(char* str) {
    for (uint32_t i = 0; i < strlen(str); i++) {
        if (str[i] >= '0' && str[i] <= '9') continue;
        if (str[i] >= 'a' && str[i] <= 'z') continue;
        if (str[i] >= 'A' && str[i] <= 'Z') continue;
        str[i] = '\0';  
    }
};

int32_t UserManager::UpdateProfile() {
    m_session->Send((uint8_t*)UPDATE_PROFILE_MSG, sizeof(UPDATE_PROFILE_MSG));
    
    uint8_t* userUpdateProfilePacket = new uint8_t[UPDATE_PROFILE_PACKET_SIZE];
    int nbytes = m_session->Recv(userUpdateProfilePacket, UPDATE_PROFILE_PACKET_SIZE);
    userUpdateProfilePacket[nbytes] = '\0';

    uint32_t delimCnt = utils::count(userUpdateProfilePacket, '|');

    if (delimCnt != 5) {
        m_session->Send((uint8_t*)UPDATE_PROFILE_FORMAT_ERROR_MSG, 
            sizeof(UPDATE_PROFILE_FORMAT_ERROR_MSG));
        delete[] userUpdateProfilePacket;
        return 1;
    }

    // write data in file
    uint32_t profilePathSize = sizeof(DIR_PATH) + strlen(m_Username)
        + sizeof(PROFILE_FILENAME) + 16;
    char* profilePath = new char[profilePathSize];
    std::memset(profilePath, 0, profilePathSize);
    std::sprintf(profilePath, "%s%s/%s", DIR_PATH, m_Username, PROFILE_FILENAME);

    std::ofstream of_Profile(profilePath);

    char* ptr = NULL;
    char* curPos = (char*)userUpdateProfilePacket;

    for (size_t i = 0; i < 5; i++) {
        ptr = strchr(curPos, '|');
        of_Profile.write(curPos, ptr - curPos);
        of_Profile.write("\n", 1);
        ptr++;
        curPos = ptr;
    }

    of_Profile.write(ptr, (char*)(userUpdateProfilePacket + nbytes) - ptr);
    of_Profile.write("\n", 1);
    of_Profile.close();
    
    delete[] profilePath;
    delete[] userUpdateProfilePacket;
    
    return 0;
};

std::vector<std::string> UserManager::ReadProfile(void) {
    std::vector<std::string> lines;

    size_t profilePathSize = sizeof(DIR_PATH) + strlen(m_Username)
        + sizeof(PROFILE_FILENAME) + 16;
    char* profilePath = new char[profilePathSize];

    std::memset(profilePath, 0, profilePathSize);
    std::sprintf(profilePath, "%s%s/%s", DIR_PATH, m_Username, PROFILE_FILENAME);

    std::ifstream Profile(profilePath);

    if (!Profile.is_open()) {
        m_session->Send((uint8_t*)NO_PROFILE_FILE, sizeof(NO_PROFILE_FILE));
        delete[] profilePath;
        return lines;
    }

    for (std::string line; std::getline(Profile, line); ) {
        lines.push_back(line);
    }
    
    delete[] profilePath;
    return lines;
};

int32_t UserManager::ViewProfile(void) {
    
    uint32_t packetSize = UPDATE_PROFILE_PACKET_SIZE + sizeof(VIEW_PROFILE_FMTSTR) + 32;
    uint8_t* packet = new uint8_t[packetSize];
    std::memset(packet, 0, packetSize);
    
    std::vector<std::string> lines = ReadProfile();

    if (lines.size() == 0) {
        return 1;
    }

    if (lines.size() < 6) {
        m_session->Send((uint8_t*)PROFILE_FORMAT_ERR, sizeof(PROFILE_FORMAT_ERR));
        return 1;
    }

    std::sprintf((char*)packet, VIEW_PROFILE_FMTSTR, 
        lines[0].c_str(), lines[1].c_str(), 
        lines[2].c_str(), lines[3].c_str(), 
        lines[4].c_str(), lines[5].c_str()
    );

    // Possible error
    m_session->Send(packet, strlen((const char*)packet)); // 
    
    delete[] packet;
    return 0;
};

int32_t UserManager::GetQR(void) {
    // check if QR-code file is already exist
    uint32_t QrCodeFilePathSize = sizeof(DIR_PATH) + strlen(m_Username) + sizeof(QR_CODE_FILENAME) + 32;
    char* QrCodeFilePath = new char[QrCodeFilePathSize];
    std::memset(QrCodeFilePath, 0, QrCodeFilePathSize);

    std::sprintf(QrCodeFilePath, "%s%s/%s", DIR_PATH, m_Username, QR_CODE_FILENAME);
    
    if (PathIsExist(QrCodeFilePath)) {
        uint32_t FileSize = utils::filesize((const char*)QrCodeFilePath);
        uint8_t* buffer = new uint8_t[FileSize];
        
        std::ifstream QrCodeFile(QrCodeFilePath);
        QrCodeFile.read((char*)buffer, FileSize);
        QrCodeFile.close();

        m_session->Send((uint8_t*)buffer, FileSize);
        
        delete[] QrCodeFilePath;
        delete[] buffer;
        return 0;
    }

    // read profile data
    std::vector<std::string> profileData = ReadProfile();

    if (profileData.size() == 0) {
        return 1;
    }

    std::string stringForQr;

    for (size_t i = 0; i < profileData.size(); i++) {
        stringForQr += profileData[i];
        stringForQr += "|";
    }

    const qrcodegen::QrCode::Ecc errCorLvl = qrcodegen::QrCode::Ecc::LOW;
    const qrcodegen::QrCode qr = qrcodegen::QrCode::encodeText(stringForQr.c_str(), errCorLvl);

    std::string stringQrCode = QrToString(qr);
    m_session->Send((uint8_t*)stringQrCode.c_str(), stringQrCode.size());

    // save to file
    std::ofstream of_QrCode(QrCodeFilePath);
    of_QrCode.write((const char*)stringQrCode.c_str(), stringQrCode.size());
    of_QrCode.close();

    delete[] QrCodeFilePath;
    return 0;
};

std::string QrToString(const qrcodegen::QrCode &qr) {
    std::string out;

	int border = 4;
	for (int y = -border; y < qr.getSize() + border; y++) {
		for (int x = -border; x < qr.getSize() + border; x++) {
			out += (qr.getModule(x, y) ? "##" : "  ");
		}
		out += "\n";
	}
	out += "\n";
    return out;
};


