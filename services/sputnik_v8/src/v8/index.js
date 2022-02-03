const { newContext, CONTEXT_CALLS } = require('./context.js');
const newSandbox = require('./sandbox.js');
const vm2 = require('vm2');

module.exports = function (code) {
    const context = newContext();
    const sandbox = newSandbox(context);
    const vm = new vm2.VM({
        timeout: 1000,
        sandbox: sandbox,
        eval: false,
        wasm: false,
        fixAsync: true,
    });
    vm.run(code);
    return new Promise((resolve, reject) => {
        let interval = setInterval(() => {
            if (context[CONTEXT_CALLS]['http.request'] >= 2) {
                resolve(context);
                if (interval !== null) {
                    clearInterval(interval);
                    interval = null;
                }
            }
        }, 100);

        setTimeout(() => {
            reject('error');
            if (interval !== null) {
                clearInterval(interval);
                interval = null;
            }
        }, 5000);
    });
};
