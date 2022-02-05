#include "main.hpp"

Proto* server = new Proto();


int main() {
    UserManager* mngr = new UserManager(server);
    while (true) {
        server->Send(MainMenu, sizeof(MainMenu));
        
        uint8_t* packet = new uint8_t[OPTION_ANSWER_PACKET_SIZE];
        server->Recv(packet, OPTION_ANSWER_PACKET_SIZE);

        bool isLoggined = false;
        switch(packet[0]) {
            case '1':
                // login
                isLoggined = mngr->Login();
                break;
            case '2':
                // reg
                isLoggined = mngr->Register();
                break;
            case '3': 
                exit(NORMAL_EXIT);
            default:
                exit(INVALID_MAIN_OPTION);
        }

        if (isLoggined) { 
            mngr->UserMenu();
        }
        
    }

    return 0;
}