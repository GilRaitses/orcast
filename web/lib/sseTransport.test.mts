// Transport-contract unit tests for the streamed-narration client (WS6 L3).
//
// There is no JS/TS unit-test runner wired in web/ (only Playwright e2e, which
// needs a live server + Bedrock and cannot deterministically exercise a stall).
// These run on Node's built-in runner with TypeScript type-stripping:
//
//   node --test lib/sseTransport.test.mts
//
// They cover the failure-fallback contract the component depends on: a stream
// that errors, ends without `done`, or stalls must REJECT (so the caller falls
// back to JSON and never hangs), while a user abort must reject WITHOUT marking
// it a stall and WITHOUT touching... well, while leaving the caller's own signal
// as the source of truth (so the component skips fallback and never double-posts).
import { test } from "node:test";
import assert from "node:assert/strict";

import { readSseStream, SseStallError } from "./sseTransport.ts";

const enc = new TextEncoder();

function frame(event: string, data: unknown): string {
  return `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
}

interface MockOpts {
  stall?: boolean;
}

function streamResponse(chunks: string[], opts: MockOpts, signal?: AbortSignal) {
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const c of chunks) controller.enqueue(enc.encode(c));
      if (opts.stall) {
        // Hold the stream open; a stall-deadline abort errors it (like real fetch).
        signal?.addEventListener("abort", () => {
          try {
            controller.error(new DOMException("aborted", "AbortError"));
          } catch {
            /* already closed */
          }
        });
      } else {
        controller.close();
      }
    },
  });
  return { ok: true, status: 200, body } as unknown as Response;
}

function mockFetch(chunks: string[], opts: MockOpts = {}) {
  (globalThis as { fetch: typeof fetch }).fetch = (async (
    _url: string,
    init: { signal?: AbortSignal },
  ) => streamResponse(chunks, opts, init?.signal)) as unknown as typeof fetch;
}

test("resolves on done and delivers tokens incrementally", async () => {
  mockFetch([
    frame("meta", { interaction_id: "i1" }),
    frame("token", { text: "Hello " }),
    frame("token", { text: "world" }),
    frame("done", { reply: "Hello world" }),
  ]);
  const tokens: string[] = [];
  let done = false;
  await readSseStream("/x", {}, { onToken: (t) => tokens.push(t), onDone: () => (done = true) });
  assert.deepEqual(tokens, ["Hello ", "world"]);
  assert.equal(done, true);
});

test("rejects on a backend error frame (so the caller falls back to JSON)", async () => {
  mockFetch([frame("meta", {}), frame("error", { error: "stream_failed", message: "boom" })]);
  await assert.rejects(readSseStream("/x", {}, { onToken: () => {} }), /boom/);
});

test("rejects on EOF before a terminal done (truncated stream -> fallback)", async () => {
  mockFetch([frame("meta", {}), frame("token", { text: "partial" })]);
  await assert.rejects(readSseStream("/x", {}, { onToken: () => {} }), /ended without done/);
});

test("stalls to SseStallError without aborting the caller's signal", async () => {
  // meta arrives but no token: the first-token deadline must fire and reject.
  mockFetch([frame("meta", {})], { stall: true });
  const ext = new AbortController();
  await assert.rejects(
    readSseStream("/x", {}, { onToken: () => {} }, ext.signal, {
      firstTokenTimeoutMs: 30,
      idleTimeoutMs: 30,
    }),
    (e) => e instanceof SseStallError,
  );
  // The caller's signal stays un-aborted: the component reads this to decide to
  // fall back to JSON (a stall is not a user cancel), so the UI never hangs.
  assert.equal(ext.signal.aborted, false);
});

test("a user abort rejects without a stall and marks the caller's signal", async () => {
  mockFetch([frame("meta", {})], { stall: true });
  const ext = new AbortController();
  const p = readSseStream("/x", {}, { onToken: () => {} }, ext.signal, {
    firstTokenTimeoutMs: 5000,
  });
  ext.abort();
  await assert.rejects(p, (e) => !(e instanceof SseStallError));
  // The component checks signal.aborted and skips fallback on a user cancel, so
  // no second (JSON) turn is posted -> no double turn.
  assert.equal(ext.signal.aborted, true);
});
