import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import net from "node:net";

import { TRSClient, TRSConnectionError, TRSValidationError } from "../dist/index.js";

function startServer(delayMs = 0) {
  const records = new Map();
  const server = http.createServer(async (req, res) => {
    if (delayMs) {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    const bodyText = Buffer.concat(chunks).toString("utf8") || "{}";
    const body = JSON.parse(bodyText);

    const send = (code, payload) => {
      const text = JSON.stringify(payload);
      res.writeHead(code, { "Content-Type": "application/json", "Content-Length": Buffer.byteLength(text) });
      res.end(text);
    };

    if (req.method === "GET" && req.url === "/health") return send(200, { status: "ok", runtime: "1.0.0", node: "0.1.0" });
    if (req.method === "POST" && req.url === "/submit") {
      const record = body.record;
      if (!record || typeof record !== "object") return send(422, { detail: "field 'record' must be an object" });
      if (!record.payload || typeof record.payload !== "object" || !("subject" in record.payload || "goal" in record.payload || "action" in record.payload)) {
        return send(200, { accepted: false, record_id: record.id ?? "", errors: ["5.3 Payload Shape"] });
      }
      records.set(record.id, record);
      return send(200, { accepted: true, record_id: record.id ?? "", errors: [] });
    }
    if (req.method === "POST" && req.url === "/query") {
      const q = body.query ?? {};
      let out = Array.from(records.values());
      if (q.type) out = out.filter((r) => r.type === q.type);
      return send(200, { records: out });
    }
    if (req.method === "POST" && req.url === "/sync") {
      const incoming = Array.isArray(body.records) ? body.records : [];
      incoming.forEach((r) => records.set(r.id, r));
      return send(200, { accepted_count: incoming.length, rejected_count: 0, appended_ids: incoming.map((r) => r.id), rejected_errors: [] });
    }
    if (req.method === "POST" && req.url === "/replay") return send(200, { coordination: { unresolved_intentions: [] } });
    return send(404, { error: "not found" });
  });
  return new Promise((resolve) => {
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      resolve({ server, url: `http://127.0.0.1:${address.port}` });
    });
  });
}

test("health, submit, query, sync, replay", async () => {
  const { server, url } = await startServer();
  try {
    const client = new TRSClient(url);
    const health = await client.health();
    assert.equal(health.status, "ok");
    await client.submit({ id: "g1", type: "Observation", payload: { subject: "boot", value: 1 } });
    const intentions = await client.query({ type: "Observation" });
    assert.equal(intentions.length, 1);
    const sync = await client.sync(intentions);
    assert.equal(sync.accepted_count, 1);
    const replay = await client.replay();
    assert.ok(replay.coordination);
  } finally {
    server.close();
  }
});

test("submit invalid raises TRSValidationError", async () => {
  const { server, url } = await startServer();
  try {
    const client = new TRSClient(url);
    await assert.rejects(async () => client.submit({ id: "bad", type: "Observation", payload: {} }), TRSValidationError);
  } finally {
    server.close();
  }
});

test("timeout raises TRSConnectionError", async () => {
  const socket = net.createServer();
  await new Promise((resolve) => socket.listen(0, "127.0.0.1", resolve));
  const address = socket.address();
  const port = address.port;
  await new Promise((resolve) => socket.close(resolve));
  const client = new TRSClient(`http://127.0.0.1:${port}`, 20);
  await assert.rejects(async () => client.health(), TRSConnectionError);
});
