require('./context.js');
const http = require('http');

Function.prototype.sandboxify = function (context, name) {
    return [...new Set(Object.getOwnPropertyNames(this))]
        .filter((method) => this[method] instanceof Function)
        .map((method) => {
            return [`context_${name}_${method}`, this[method].contextify(context, `${name}.${method}`)];
        })
        .concat([
            [
                `context_${name}_constructor`,
                ((...args) => Reflect.construct(this, args)).contextify(context, `${name}.constructor`),
            ],
        ])
        .reduce((cc, props) => Object.assign(cc, { [props[0]]: props[1] }), {});
};

module.exports = (context) =>
    ['console.log', 'JSON.parse', 'JSON.stringify', 'http.request'].reduce(
        (cc, fn) => Object.assign(cc, { [`context_${fn.replace('.', '_')}`]: eval(fn).contextify(context, fn) }),
        [
            'Set',
            'Map',
            'Buffer',
            'Int8Array',
            'Uint8Array',
            'Int16Array',
            'Uint16Array',
            'Int32Array',
            'Uint32Array',
        ].reduce((cc, obj) => Object.assign(cc, eval(obj).sandboxify(context, obj)), {})
    );
