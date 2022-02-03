const [CONTEXT_CALLS] = ['CALLS'];

const newContext = () => ({
    [CONTEXT_CALLS]: {},
});

Function.prototype.contextify = function (context, name) {
    let original = this;
    if (this.__original) {
        original = this.__original;
    }

    const ret = function () {
        context[CONTEXT_CALLS][name] =
            (context[CONTEXT_CALLS][name] === undefined ? 0 : context[CONTEXT_CALLS][name]) + 1;
        return original.apply(this, arguments);
    };

    ret.__original = original;

    return ret;
};

module.exports = {
    newContext,
    CONTEXT_CALLS,
};
