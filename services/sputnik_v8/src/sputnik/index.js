const { translate, validateOpcode } = require('./opcodes.js');
const vmExecute = require('../v8');

const execute = (opcodes, vmId, apiKey, gasLeft, reportAddress) => {
    const template = `let tmp = null;
let obj = null;
let args = [];
let vmId = "${vmId}";
let apiKey = "${apiKey}";
let gasLeft = ${gasLeft};
let reported = false;
stack = [];
  
const validateValue = (value) => {
    if (typeof value === 'number') {
        return -1024 <= value && value < 1024;
    }
    if (typeof value.length === 'number') {
        return value.length <= 1024;
    }
    if (typeof value.size === 'number') {
        return value.size <= 1024;
    }
    return true;
};
const checkStack = () => {
    if (!stack.every(validateValue)) {
        throw 'invalid value on stack';
    }
    if (stack.length > 256) {
        throw 'stack size too big';
    }
};
const checkStackSizeAtLeast = (n) => {
    if (stack.length < n) {
        throw 'stack size too small';
    }
};
const checkStackNotEmpty = () => checkStackSizeAtLeast(1);
const checkStackTopNumberPositive = () => {
    if (typeof stack[stack.length-1] !== 'number' || stack[stack.length-1] <= 0) {
        throw 'value is not positive';
    }
};
const report = (value) => {
    if (reported) {
        return;
    }
    if (typeof value.toString !== 'function') {
        throw 'trying to report bad value';
    }
    value = value.toString();
    if (typeof value !== 'string') {
        throw 'trying to report bad balue after toString';
    }
    if (value.length > 1024) {
        throw 'trying to report long string';
    }
    reported = true;
    const data = context_JSON_stringify({
        value: value,
    });
    const req = context_http_request({
        method: 'POST',
        host: '${reportAddress}',
        family: '4',
        port: 5678,
        path: '/api/executor/postReport?vmId=' + vmId + '&apiKey=' + apiKey,
        timeout: 1000,
        headers: {
            'Content-Type': 'application/json'
        }
    });
    req.on('error', () => {});
    req.write(data);
    req.end();
};
const consumeGas = () => {
    gasLeft -= 1;
    if (gasLeft < 0) {
        throw 'not enough gas left';
    }
};

const main = () => {
TEMPLATE_CODE
};
let oldReport = '';
const req = context_http_request({
    host: '${reportAddress}',
    family: '4',
    port: 5678,
    path: '/api/executor/getReport?vmId=' + vmId + '&apiKey=' + apiKey,
    timeout: 1000,
    headers: {
        'Content-Type': 'application/json'
    }
}, (response) => {
    response.on('data', (chunk) => {
        oldReport += chunk;
    });
    response.on('end', () => {
        try {
            oldReport = JSON.parse(oldReport);
            let { ok = false, result = "" } = oldReport;
            if (!ok || typeof result !== 'string') {
                report('empty')
            } else {
                stack.push(result);
                main();
                report('empty');
            }
        } catch (e) {
            try {
                if (typeof e === 'string') {
                    report(e);
                } else {
                    report('empty');
                }
            } catch(_) {
                report('empty');
            }
        }
    });
});
req.on('error', () => { report('empty'); });
req.end();
`;

    let program = '';
    let opcodeNum = 0;

    for (const opcode of opcodes) {
        if (!validateOpcode(opcode, opcodeNum)) {
            return { ok: false, error: 'invalid opcode' };
        }
        program += `    opcode${opcodeNum}:while(true){consumeGas();${translate(
            opcode,
            opcodeNum
        )};checkStack()\n`;
        opcodeNum += 1;
    }

    program += '    ' + 'break;}'.repeat(opcodeNum);
    program = template.replace('TEMPLATE_CODE', program);

    return { ok: true, result: vmExecute(program) };
};

module.exports = execute;
