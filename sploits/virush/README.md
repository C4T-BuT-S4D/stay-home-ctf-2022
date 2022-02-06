# STAY ~/ CTF 2022: VACCINATED EDITION

## virush

Author: [@keltecc](https://github.com/keltecc)

### Overview

The service is a simple key-value storage.

Users can REGISTER and PUT some information to storage, also they can GET the information back.

In order to store protected information, users can choose ENCRYPTED option, then the information will be stored as encrypted data inside the storage.

### Vuln 1: crypto

TLDR:

1. Read a hidden `.hash` file that contains a [SHA-256 hash](https://en.wikipedia.org/wiki/SHA-2) of user's password
2. [OpenSSL](https://en.wikipedia.org/wiki/OpenSSL) is running with `-iter 16` option, which is using [PBKDF2](https://en.wikipedia.org/wiki/PBKDF2) function internal
3. Exploit a well-known property of PBKDF2 which is described in Wikipedia article (`HMAC collisions`)
4. Decrypt the `flag` content using a password hash from `.hash` file (we don't really need the actual password)

Exploit: [vuln1_pbkdf2.py](vuln1_pbkdf2.py)

FIX:

Hide the `.hash` file somehow (rename/move/etc).

### Vuln 2: RCE

TLDR:

1. The service doesn't quote arguments of commands (for example: `openssl ${CipherAlgorithm} -e -iter 16 -k ${key} -iv ${iv}`)
2. So we can control arguments of most commands, it may lead to vulnerability
3. `dd` command is interesting: we can set `of=/proc/self/mem` and overwrite the process memory!
4. Also we can set `seek=0x7ffc00000000` to jump somewhere near the stack (this is a lower bound address)
5. So now we need to leak actual stack pointer, we will find a PID of running `dd` and read `/proc/PID/stat`
6. The we will read `/proc/PID/maps` and leak the libc mapping
7. We need to make another seek from `0x7ffc00000000` to real stack address
8. So we will also set a `conv=sparse` argument to `dd` and it will perform seek instead of writing `\x00` bytes (wow!)
9. When we have reached the `ret` of some function, just write a ROP chain and execute `system`
10. In order to make `dd` run infinitely, we will set `if=/proc/self/fd/255` (this is a special FD [used by Bash](https://stackoverflow.com/q/29729906))

More detailed description could be found in exploit: [vuln2_rce.py](vuln2_rce.py)

FIX:

Wrap commands' arguments with quotes, for example: `openssl "${CipherAlgorithm}" -e -iter 16 -k "${key}" -iv "${iv}"`
