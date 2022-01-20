const execute = require('../sputnik');
const express = require('express');
const app = express();

app.use(express.json());

app.post('/api/execute', (req, res) => {
    const { opcodes = [], vmId = '', apiKey = '' } = req.body;
    if (!Array.isArray(opcodes)) {
        res.json({ ok: false, error: 'invalid opcodes type' });
        return;
    }

    for (const opcode of opcodes) {
        if (!Array.isArray(opcode) || opcode.length < 1 || typeof opcode[0] !== 'string') {
            res.json({ ok: false, error: 'invalid opcode' });
            return;
        }
    }

    if (typeof vmId !== 'string' || !/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/.test(vmId)) {
        res.json({ ok: false, error: 'invalid vmId' });
        return;
    }

    if (typeof apiKey !== 'string' || !/^API_[A-Z2-7]{16}_KEY$/.test(apiKey)) {
        res.json({ ok: false, error: 'invalid apiKey' });
        return;
    }

    const p = execute(
        opcodes,
        vmId,
        apiKey,
        1e6,
        process.env.REPORTER_ADDRESS ? process.env.REPORTER_ADDRESS : 'localhost'
    );

    p.then((context) => res.json({ ok: true, result: context })).catch(() =>
        res.json({ ok: false, error: 'unexpected error' })
    );
});

const port = 1337;
app.listen(port, () => {
    console.log(`Executor listening at :${port}`);
});
