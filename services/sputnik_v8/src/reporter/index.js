const http = require('http');
const { v4: uuidv4 } = require('uuid');
const { Pool } = require('pg');
const db = new Pool({
    user: 'sputnik',
    host: process.env.DATABASE_ADDRESS ? process.env.DATABASE_ADDRESS : 'localhost',
    database: 'sputnik',
    password: 'sputnik',
    port: 5432,
});
const express = require('express');
const app = express();

app.use(express.json());

app.post('/api/execute', (req, res) => {
    const { accessKey = '' } = req.query;
    const { opcodes = [], report = 'empty' } = req.body;
    const vmId = uuidv4();
    const apiKey = `API_${process.env.API_KEY ? process.env.API_KEY : ''}_KEY`;

    if (
        typeof accessKey !== 'string' ||
        !/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/.test(accessKey)
    ) {
        res.json({ ok: false, error: 'invalid accessKey' });
        return;
    }

    if (typeof report !== 'string' || report.length > 1024) {
        res.json({ ok: false, error: 'invalid report' });
        return;
    }

    db.query(
        'INSERT INTO vms (id, accessKey, report) VALUES ($1, $2, $3)',
        [vmId, accessKey, Buffer.from(report)],
        (err) => {
            if (err) {
                res.json({ ok: false, error: "can't insert new vm" });
            } else {
                let data = JSON.stringify({ opcodes, vmId, apiKey });
                let result = '';

                const request = http.request(
                    {
                        method: 'POST',
                        host: process.env.EXECUTOR_ADDRESS ? process.env.EXECUTOR_ADDRESS : 'localhost',
                        family: '4',
                        port: 1337,
                        path: '/api/execute',
                        timeout: 1000,
                        headers: {
                            'Content-Type': 'application/json',
                        },
                    },
                    (response) => {
                        response.on('data', (chunk) => {
                            result += chunk;
                        });
                        response.on('end', () => {
                            try {
                                let context = JSON.parse(result);
                                if (context.ok) {
                                    db.query('UPDATE vms SET context=$1 WHERE id=$2', [context.result, vmId], (err) => {
                                        if (err) {
                                            res.json({ ok: false, error: "can't update vm context" });
                                        } else {
                                            res.json({
                                                ok: true,
                                                result: {
                                                    context: context.result,
                                                    vmId,
                                                },
                                            });
                                        }
                                    });
                                } else {
                                    res.json({ ok: false, error: context.error });
                                }
                            } catch (e) {
                                res.json({ ok: false, error: 'unexpected error' });
                            }
                        });
                    }
                );
                request.on('error', () => {
                    res.json({ ok: false, error: 'unexpected error' });
                });
                request.write(data);
                request.end();
            }
        }
    );
});

app.post('/api/executor/postReport', (req, res) => {
    const { vmId = '', apiKey = '' } = req.query;
    const { value = '' } = req.body;

    if (typeof vmId !== 'string' || !/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/.test(vmId)) {
        res.json({ ok: false, error: 'invalid vmId' });
        return;
    }

    if (
        typeof apiKey !== 'string' ||
        !/^API_[A-Z2-7]{16}_KEY$/.test(apiKey) ||
        apiKey !== `API_${process.env.API_KEY ? process.env.API_KEY : ''}_KEY`
    ) {
        res.json({ ok: false, error: 'invalid apiKey' });
        return;
    }

    if (typeof value !== 'string' || value.length > 1024) {
        res.json({ ok: false, error: 'invalid value' });
        return;
    }

    db.query('UPDATE vms SET report=$1 WHERE id=$2', [Buffer.from(value), vmId], (err) => {
        if (err) {
            res.json({ ok: false, error: "can't update vm result" });
        } else {
            res.json({ ok: true, result: null });
        }
    });
});

app.get('/api/getReport', (req, res) => {
    const { vmId = '', accessKey = '' } = req.query;

    if (typeof vmId !== 'string' || !/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/.test(vmId)) {
        res.json({ ok: false, error: 'invalid vmId' });
        return;
    }

    if (
        typeof accessKey !== 'string' ||
        !/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/.test(accessKey)
    ) {
        res.json({ ok: false, error: 'invalid accessKey' });
        return;
    }

    db.query('SELECT report FROM vms WHERE id=$1 AND accessKey=$2', [vmId, accessKey], (err, data) => {
        if (err) {
            res.json({ ok: false, error: "can't select vm report" });
        } else {
            if (data.rowCount === 0) {
                res.json({ ok: false, error: 'no such vm' });
            } else {
                res.json({ ok: true, result: data.rows[0].report.toString() });
            }
        }
    });
});

app.get('/api/executor/getReport', (req, res) => {
    const { vmId = '', apiKey = '' } = req.query;

    if (typeof vmId !== 'string' || !/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/.test(vmId)) {
        res.json({ ok: false, error: 'invalid vmId' });
        return;
    }

    if (
        typeof apiKey !== 'string' ||
        !/^API_[A-Z2-7]{16}_KEY$/.test(apiKey) ||
        apiKey !== `API_${process.env.API_KEY ? process.env.API_KEY : ''}_KEY`
    ) {
        res.json({ ok: false, error: 'invalid apiKey' });
        return;
    }

    db.query('SELECT report FROM vms WHERE id=$1', [vmId], (err, data) => {
        if (err) {
            res.json({ ok: false, error: "can't select vm report" });
        } else {
            if (data.rowCount === 0) {
                res.json({ ok: false, error: 'no such vm' });
            } else {
                res.json({ ok: true, result: data.rows[0].report.toString() });
            }
        }
    });
});

const port = 5678;
db.query(
    "CREATE TABLE IF NOT EXISTS vms (id UUID PRIMARY KEY, accessKey UUID, report BYTEA NOT NULL DEFAULT 'empty', context VARCHAR NOT NULL DEFAULT '{\"CALLS\": {}}')",
    (err) => {
        if (err) {
            console.error("Can't init postgres schema", err);
        } else {
            app.listen(port, () => {
                console.log(`Reporter listening at :${port}`);
            });
        }
    }
);
