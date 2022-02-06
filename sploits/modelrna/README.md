# STAY ~/ CTF 2022: VACCINATED EDITION

## modelrna

Author: [@jnovikov](https://github.com/jnovikov)

### Overview

The service is a platform that can allow users to create the vaccines and upload the ML-models that other users can
use to check does the vaccine work for them.

The models are uploaded in the ONNX-format and encrypted using ChaCha20 algorithm.

There is no vulnerabilities in the provided code, the vulnerability itself in the onnxruntime library.
 
### Vuln: LFD while loading model (kind of 0-day)

Explanation:
1. User can upload any correct onnx model to the service that have 1 input (scalar of 5 elements) and 1 or 2 outputs. 
2. The onnx model itself is just a encoded protobuf that have a VM-like operations and described inputs/outputs tensors. 
3. ONNX Tensor proto have a ["external_data" field](https://github.com/onnx/onnx/blob/main/onnx/onnx.proto#L596). This field has a "location" key which references to the relative path at the FS.    
4. There is no checks in the onnxruntime that will block the malicious file-paths (but there are some in the onnx python-library which is not used by onnxruntime).

Exploitation:

To do the exploitation you will need to create ML model that will read the contents of the /app/config.env file which has a JWT secret key used to sign user-requests.

You should build the model that will not fail with the data provided from service (5 values).

Steps:
1. Create const tensor that will reference to the ../../../app/config.env of size 8 type INT64. 
This will help us to leak 40 bytes of the file (you also can set "offset" field to leak any part of the file).
2. Sum this tensor with the user-provided tensor/input.
3. Output the result (pls note there is no checks on output tensor size, the output should have 1 or 2 output tensors, but there is no restrictions on the size of these tensors).
4. Call the model using service (test the vaccine) with all zeros data to leak the config file.
5. Convert int bytes to string and find the JWT key.
6. Use the JWT key to sign requests and login as any user.

Exploit: [lfd_secret_key_leak.py](lfd_secret_key_leak.py)

FIX:

Find '../' pattern in the decrypted bytes of the uploaded model (the strings can be found as is in the protocol buffers).
