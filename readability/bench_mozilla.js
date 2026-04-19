#!/usr/bin/env node
/**
 * Benchmark helper: run Mozilla Readability.js on a single HTML file.
 *
 * Usage:
 *   node bench_mozilla.js <html_file> [rounds]
 *
 * Outputs JSON:
 *   { "file": "...", "rounds": N, "times_ms": [...], "min_ms": ...,
 *     "mean_ms": ..., "max_ms": ..., "title": "...", "length": N }
 */

const fs = require("fs");
const { JSDOM } = require("jsdom");
const { Readability, isProbablyReaderable } = require("@mozilla/readability");

const htmlFile = process.argv[2];
const rounds = parseInt(process.argv[3] || "10", 10);

if (!htmlFile) {
  console.error("Usage: node bench_mozilla.js <html_file> [rounds]");
  process.exit(1);
}

const html = fs.readFileSync(htmlFile, "utf-8");
const times = [];

// Warm-up run (not counted).
{
  const dom = new JSDOM(html);
  new Readability(dom.window.document).parse();
}

for (let i = 0; i < rounds; i++) {
  const start = process.hrtime.bigint();
  const dom = new JSDOM(html);
  const article = new Readability(dom.window.document).parse();
  const end = process.hrtime.bigint();
  const elapsed = Number(end - start) / 1e6; // ns -> ms
  times.push(elapsed);
}

// Grab metadata from last run for verification.
const dom = new JSDOM(html);
const article = new Readability(dom.window.document).parse();

const result = {
  file: htmlFile,
  rounds: rounds,
  times_ms: times,
  min_ms: Math.min(...times),
  mean_ms: times.reduce((a, b) => a + b, 0) / times.length,
  max_ms: Math.max(...times),
  title: article ? article.title : null,
  length: article ? article.textContent.length : 0,
};

console.log(JSON.stringify(result));
