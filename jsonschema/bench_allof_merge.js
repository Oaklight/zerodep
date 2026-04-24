#!/usr/bin/env node
/**
 * Benchmark helper: run allof-merge on JSON Schema read from stdin.
 *
 * Usage:
 *   echo '{"allOf":[...]}' | node bench_allof_merge.js [rounds]
 *
 * Outputs JSON:
 *   { "rounds": N, "times_ms": [...], "min_ms": ...,
 *     "mean_ms": ..., "max_ms": ..., "result": {...} }
 */

const { merge } = require("allof-merge");

const rounds = parseInt(process.argv[2] || "10", 10);

let input = "";
process.stdin.setEncoding("utf-8");
process.stdin.on("data", (chunk) => (input += chunk));
process.stdin.on("end", () => {
  const schema = JSON.parse(input);
  const times = [];

  // Warm-up run (not counted).
  merge(structuredClone(schema));

  for (let i = 0; i < rounds; i++) {
    const copy = structuredClone(schema);
    const start = process.hrtime.bigint();
    merge(copy);
    const end = process.hrtime.bigint();
    times.push(Number(end - start) / 1e6); // ns -> ms
  }

  // Final run for result capture.
  const result = merge(structuredClone(schema));

  const output = {
    rounds: rounds,
    times_ms: times,
    min_ms: Math.min(...times),
    mean_ms: times.reduce((a, b) => a + b, 0) / times.length,
    max_ms: Math.max(...times),
    result: result,
  };

  console.log(JSON.stringify(output));
});
