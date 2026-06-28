#!/usr/bin/env node
// WS2 measurement harness — fetch + getReader() client.
//
// PURPOSE
//   Connect to a probe URL, read the SSE byte stream incrementally, and record
//   the client-side arrival timestamp of every `event: token` frame. Computes
//   first-token latency and decides incremental-vs-all-at-once. Emits a
//   machine-readable JSON result the BENCHMARK_REPORT can cite.
//
//   This mirrors how the real client will read (web/lib/adaptiveConsole.ts will
//   move from res.json() to res.body.getReader()), so it measures the same path
//   the product will use. EventSource is NOT used (POST + body; GET-only limit).
//
// USAGE
//   node measure_stream.mjs <url> [--method GET|POST] [--label NAME] [--out FILE]
//   examples:
//     node measure_stream.mjs http://127.0.0.1:8099/__stream_probe --label direct-uvicorn
//     node measure_stream.mjs https://orcast-api.aimez.ai/__stream_probe --label cloudflared
//     node measure_stream.mjs https://<preview>.vercel.app/api/__streamprobe --label vercel
//
// INCREMENTAL TEST
//   If every token arrives in one burst (all inter-arrival gaps near zero and the
//   first token arrives only at/after the server's total emit window), a layer
//   buffered. If tokens arrive spread ~interval apart, the chain is unbuffered.
//   The harness flags `incremental: true/false` using a gap heuristic plus the
//   span ratio (client span vs expected server span).

import { writeFileSync } from "node:fs";
import { performance } from "node:perf_hooks";

function parseArgs(argv) {
  const args = { method: "GET", label: "probe", out: null };
  const positional = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--method") args.method = argv[++i];
    else if (a === "--label") args.label = argv[++i];
    else if (a === "--out") args.out = argv[++i];
    else positional.push(a);
  }
  args.url = positional[0];
  return args;
}

function parseSseFrames(buffer) {
  // Returns [frames, remainder]. A frame ends at a blank line (\n\n).
  const frames = [];
  let rest = buffer;
  let idx;
  while ((idx = rest.indexOf("\n\n")) !== -1) {
    const raw = rest.slice(0, idx);
    rest = rest.slice(idx + 2);
    let event = "message";
    const dataLines = [];
    for (const line of raw.split("\n")) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
    }
    frames.push({ event, data: dataLines.join("\n") });
  }
  return [frames, rest];
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.url) {
    console.error("usage: node measure_stream.mjs <url> [--method GET|POST] [--label NAME] [--out FILE]");
    process.exit(2);
  }

  const init = { method: args.method, headers: { Accept: "text/event-stream" }, cache: "no-store" };
  if (args.method === "POST") {
    init.headers["Content-Type"] = "application/json";
    init.body = JSON.stringify({ probe: true });
  }

  const t0 = performance.now();
  let firstByteMs = null;
  const tokenArrivals = []; // { i, client_ms, server_ts }
  let metaMs = null;
  let doneMs = null;

  const resp = await fetch(args.url, init);
  if (!resp.ok || !resp.body) {
    console.error(`HTTP ${resp.status} or no body for ${args.url}`);
    process.exit(1);
  }

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    if (firstByteMs === null) firstByteMs = performance.now() - t0;
    buf += decoder.decode(value, { stream: true });
    const [frames, rest] = parseSseFrames(buf);
    buf = rest;
    for (const f of frames) {
      const nowMs = performance.now() - t0;
      let payload = {};
      try { payload = JSON.parse(f.data); } catch { /* tolerate */ }
      if (f.event === "meta") metaMs = nowMs;
      else if (f.event === "token") tokenArrivals.push({ i: payload.i, client_ms: nowMs, server_ts: payload.server_ts });
      else if (f.event === "done") doneMs = nowMs;
    }
  }

  // Inter-arrival gaps between consecutive token frames (client side).
  const gaps = [];
  for (let i = 1; i < tokenArrivals.length; i++) {
    gaps.push(tokenArrivals[i].client_ms - tokenArrivals[i - 1].client_ms);
  }
  const firstTokenMs = tokenArrivals.length ? tokenArrivals[0].client_ms : null;
  const lastTokenMs = tokenArrivals.length ? tokenArrivals[tokenArrivals.length - 1].client_ms : null;
  const clientSpanMs = firstTokenMs !== null && lastTokenMs !== null ? lastTokenMs - firstTokenMs : 0;
  const medianGap = gaps.length ? [...gaps].sort((a, b) => a - b)[Math.floor(gaps.length / 2)] : 0;

  // Incremental heuristic: tokens are spread out (median gap > 20 ms) AND the
  // overall client span is a meaningful fraction of the expected server emit
  // window. Buffered streams collapse all tokens into one burst (span ~0).
  const incremental = medianGap > 20 && clientSpanMs > 50;

  const result = {
    label: args.label,
    url: args.url,
    method: args.method,
    http_status: resp.status,
    content_type: resp.headers.get("content-type"),
    first_byte_ms: firstByteMs !== null ? Math.round(firstByteMs) : null,
    first_token_ms: firstTokenMs !== null ? Math.round(firstTokenMs) : null,
    meta_ms: metaMs !== null ? Math.round(metaMs) : null,
    done_ms: doneMs !== null ? Math.round(doneMs) : null,
    token_count: tokenArrivals.length,
    client_span_ms: Math.round(clientSpanMs),
    median_gap_ms: Math.round(medianGap),
    gaps_ms: gaps.map((g) => Math.round(g)),
    incremental,
    first_token_under_1500ms: firstTokenMs !== null ? firstTokenMs <= 1500 : null,
    verdict: incremental && firstTokenMs !== null && firstTokenMs <= 1500 ? "PASS" : "FAIL/INVESTIGATE",
    captured_at: new Date().toISOString(),
  };

  const json = JSON.stringify(result, null, 2);
  console.log(json);
  if (args.out) {
    writeFileSync(args.out, json + "\n");
    console.error(`wrote ${args.out}`);
  }
}

main().catch((e) => { console.error(e); process.exit(1); });
