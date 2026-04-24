#!/usr/bin/env node
/**
 * Persistent benchmark server for allof-merge.
 *
 * Reads JSON commands from stdin (one per line) and writes JSON
 * results to stdout.  Keeps the Node.js process alive so that
 * pytest-benchmark can measure merge time without subprocess
 * startup overhead.
 *
 * Protocol:
 *   Request:  {"schema": {...}}
 *   Response: {"ok": true, "time_ms": 0.12, "result": {...}}
 *
 *   Send {"cmd": "quit"} to shut down gracefully.
 */

const readline = require("readline");
const { merge } = require("allof-merge");

// Warm-up: run merge once to JIT-compile hot paths.
merge({ type: "object", properties: { a: { type: "string" } } });

const rl = readline.createInterface({ input: process.stdin });

// Signal readiness.
process.stdout.write(JSON.stringify({ ready: true }) + "\n");

rl.on("line", (line) => {
  let req;
  try {
    req = JSON.parse(line);
  } catch {
    process.stdout.write(
      JSON.stringify({ ok: false, error: "invalid JSON" }) + "\n",
    );
    return;
  }

  if (req.cmd === "quit") {
    process.exit(0);
  }

  if (!req.schema) {
    process.stdout.write(
      JSON.stringify({ ok: false, error: "need 'schema'" }) + "\n",
    );
    return;
  }

  try {
    const copy = structuredClone(req.schema);
    const start = process.hrtime.bigint();
    const result = merge(copy);
    const end = process.hrtime.bigint();
    const elapsed = Number(end - start) / 1e6; // ns -> ms

    process.stdout.write(
      JSON.stringify({ ok: true, time_ms: elapsed, result: result }) + "\n",
    );
  } catch (e) {
    process.stdout.write(
      JSON.stringify({ ok: false, error: e.message }) + "\n",
    );
  }
});
