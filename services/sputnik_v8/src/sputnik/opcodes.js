const [
    OP_PUSH,
    OP_POP,
    OP_DUP,
    OP_SWAP,
    OP_HIDE,
    OP_CALL,
    OP_INVOKE,
    OP_RESET,
    OP_JMP,
    OP_JMPIF,
    OP_JMPNIF,
    OP_REPORT,
    OP_ADD,
    OP_SUB,
    OP_HLTCHK,
    OP_HLTNCHK,
] = [
    'OP_PUSH',
    'OP_POP',
    'OP_DUP',
    'OP_SWAP',
    'OP_HIDE',
    'OP_CALL',
    'OP_INVOKE',
    'OP_RESET',
    'OP_JMP',
    'OP_JMPIF',
    'OP_JMPNIF',
    'OP_REPORT',
    'OP_ADD',
    'OP_SUB',
    'OP_HLTCHK',
    'OP_HLTNCHK',
];

const translate = (opcode, opcodeNum) => {
    switch (opcode[0]) {
        case OP_PUSH:
            return `stack.push(${typeof opcode[1] === 'number' ? opcode[1] : "'" + opcode[1] + "'"})`;
        case OP_POP:
            return 'checkStackNotEmpty();stack.pop()';
        case OP_DUP:
            return 'checkStackNotEmpty();stack.push(stack[stack.length - 1])';
        case OP_SWAP:
            return 'checkStackSizeAtLeast(2);tmp=stack[stack.length-2];stack[stack.length-2]=stack[stack.length-1];stack[stack.length-1]=tmp';
        case OP_HIDE:
            return 'checkStackSizeAtLeast(3);tmp=stack[stack.length-2];stack[stack.length-2]=stack[stack.length-1];stack[stack.length-1]=tmp;tmp=stack[stack.length-3];stack[stack.length-3]=stack[stack.length-2];stack[stack.length-2]=tmp';
        case OP_CALL:
            return `checkStackNotEmpty();checkStackTopNumberNonNegative();tmp=stack.pop();checkStackSizeAtLeast(tmp);while(tmp-->0)args.push(stack.pop());stack.push(${opcode[1]}.apply(undefined, args));args=[]`;
        case OP_INVOKE:
            return `checkStackSizeAtLeast(2);obj=stack.pop();checkStackTopNumberNonNegative();tmp=stack.pop();checkStackSizeAtLeast(tmp);while(tmp-->0)args.push(stack.pop());stack.push(obj.${opcode[1]}.apply(obj, args));args=[]`;
        case OP_RESET:
            return 'stack=[]';
        case OP_JMP:
            return `continue opcode${opcodeNum - opcode[1]}`;
        case OP_JMPIF:
            return `checkStackNotEmpty();if(!stack.pop())continue opcode${opcodeNum - opcode[1]}`;
        case OP_JMPNIF:
            return `checkStackNotEmpty();if(stack.pop())continue opcode${opcodeNum - opcode[1]}`;
        case OP_REPORT:
            return `checkStackNotEmpty();report(stack.pop())`;
        case OP_ADD:
            return 'checkStackSizeAtLeast(2);stack.push(stack.pop()+stack.pop())';
        case OP_SUB:
            return 'checkStackSizeAtLeast(2);stack.push(stack.pop()-stack.pop())';
        case OP_HLTCHK:
            return 'checkStackSizeAtLeast(2);if(!stack.pop()){report(stack.pop());return;}';
        case OP_HLTNCHK:
            return 'checkStackSizeAtLeast(2);if(stack.pop()){report(stack.pop());return;}';
    }
};

const validateOpcodeNumber = (value) => {
    return typeof value === 'number' && -1024 <= value && value < 1024;
};

const validateOpcodeString = (value) => {
    return typeof value === 'string' && value.length <= 1024;
};

const validateOpcodeValue = (value) => validateOpcodeNumber(value) || validateOpcodeString(value);

const validateOpcode = (opcode, opcodeNum) => {
    switch (opcode[0]) {
        case OP_PUSH:
            return (
                opcode.length === 2 &&
                validateOpcodeValue(opcode[1]) &&
                (typeof opcode[1] !== 'string' || /^[A-Za-z0-9=_]*$/.test(opcode[1]))
            );
        case OP_POP:
            return opcode.length === 1;
        case OP_DUP:
            return opcode.length === 1;
        case OP_SWAP:
            return opcode.length === 1;
        case OP_HIDE:
            return opcode.length === 1;
        case OP_CALL:
            return (
                opcode.length === 2 &&
                validateOpcodeString(opcode[1]) &&
                /^context_[A-Za-z0-9_]+$/.test(opcode[1]) &&
                !/http/.test(opcode[1])
            );
        case OP_INVOKE:
            return (
                opcode.length === 2 &&
                validateOpcodeString(opcode[1]) &&
                /^[A-Za-z0-9]+$/.test(opcode[1]) &&
                !/prot|glob|eval|Func|func|cons|def|__/.test(opcode[1])
            );
        case OP_RESET:
            return opcode.length === 1;
        case OP_JMP:
            return opcode.length === 2 && validateOpcodeNumber(opcode[1]) && opcodeNum - opcode[1] >= 0;
        case OP_JMPIF:
            return opcode.length === 2 && validateOpcodeNumber(opcode[1]) && opcodeNum - opcode[1] >= 0;
        case OP_JMPNIF:
            return opcode.length === 2 && validateOpcodeNumber(opcode[1]) && opcodeNum - opcode[1] >= 0;
        case OP_REPORT:
            return opcode.length === 1;
        case OP_ADD:
            return opcode.length === 1;
        case OP_SUB:
            return opcode.length === 1;
        case OP_HLTCHK:
            return opcode.length === 1;
        case OP_HLTNCHK:
            return opcode.length === 1;
        default:
            return false;
    }
};

module.exports = { validateOpcode, translate };
