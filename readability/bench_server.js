#!/usr/bin/env node
/**
 * Persistent benchmark server for Mozilla Readability.js.
 *
 * Reads JSON commands from stdin (one per line) and writes JSON
 * results to stdout.  Keeps the Node.js process alive so that
 * pytest-benchmark can measure parse time without subprocess
 * startup overhead.
 *
 * Protocol:
 *   Request:  {"file": "/path/to/source.html"}
 *             or {"html": "<html>...</html>"}
 *   Response: {"ok": true, "time_ms": 12.34, "title": "...", "length": 123}
 *
 *   Send {"cmd": "quit"} to shut down gracefully.
 */

const fs = require("fs");
const readline = require("readline");
const { JSDOM } = require("jsdom");
const { Readability } = require("@mozilla/readability");

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

  let html;
  try {
    if (req.file) {
      html = fs.readFileSync(req.file, "utf-8");
    } else if (req.html) {
      html = req.html;
    } else {
      process.stdout.write(
        JSON.stringify({ ok: false, error: "need 'file' or 'html'" }) + "\n",
      );
      return;
    }
  } catch (e) {
    process.stdout.write(
      JSON.stringify({ ok: false, error: e.message }) + "\n",
    );
    return;
  }

  const start = process.hrtime.bigint();
  const dom = new JSDOM(html);
  const article = new Readability(dom.window.document).parse();
  const end = process.hrtime.bigint();
  const elapsed = Number(end - start) / 1e6; // ns -> ms

  process.stdout.write(
    JSON.stringify({
      ok: true,
      time_ms: elapsed,
      title: article ? article.title : null,
      length: article ? article.textContent.length : 0,
    }) + "\n",
  );
});
