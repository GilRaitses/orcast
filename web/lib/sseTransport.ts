// Reusable SSE transport client (WS-STREAM consumer #1: streamed narration).
//
// A thin `fetch` + `getReader()` reader for Server-Sent Events with named events
// (meta / token / done / error). EventSource is not used because the narrate
// stream is a POST with a JSON body. Frame parsing buffers partial reads so a
// frame split across two network chunks is reassembled correctly.
//
// This module owns ONLY the transport edge: bytes, frame parsing, and abort. It
// has no narration semantics; callers map the parsed events onto their domain.

export interface SseEvent {
  event: string;
  data: string;
}

export interface SseHandlers {
  onMeta?: (data: unknown) => void;
  onToken?: (text: string) => void;
  onDone?: (data: unknown) => void;
  onError?: (data: unknown) => void;
}

export interface SseStreamOptions {
  // Abort + reject if no first token arrives within this window (e.g. App Runner
  // cold start, edge holding the response open). Defaults below.
  firstTokenTimeoutMs?: number;
  // Abort + reject if the gap between tokens exceeds this window.
  idleTimeoutMs?: number;
}

const DEFAULT_FIRST_TOKEN_TIMEOUT_MS = 10_000;
const DEFAULT_IDLE_TIMEOUT_MS = 15_000;

// Thrown when a stall deadline fires (NOT a user abort). The caller distinguishes
// this from a user-initiated abort by checking its own AbortSignal, and falls
// back to the non-streamed path on a stall.
export class SseStallError extends Error {
  constructor(message = "sse stream stalled") {
    super(message);
    this.name = "SseStallError";
  }
}

function parseFrames(buffer: string): { frames: SseEvent[]; rest: string } {
  const frames: SseEvent[] = [];
  let rest = buffer;
  let idx: number;
  while ((idx = rest.indexOf("\n\n")) !== -1) {
    const raw = rest.slice(0, idx);
    rest = rest.slice(idx + 2);
    let event = "message";
    const dataLines: string[] = [];
    for (const line of raw.split("\n")) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
    }
    if (dataLines.length || event !== "message") {
      frames.push({ event, data: dataLines.join("\n") });
    }
  }
  return { frames, rest };
}

function safeParse(data: string): unknown {
  try {
    return JSON.parse(data);
  } catch {
    return data;
  }
}

// Open an SSE POST stream and dispatch named events to the handlers. Resolves
// only after a terminal `done` event. Rejects on: a non-OK response, a parsed
// `error` event, a stall (no first token / idle gap exceeds the deadline), a
// user abort, or EOF before a terminal frame. Callers fall back to the
// non-streamed path on any rejection that is not a user abort, so the UI never
// hangs waiting on a silent stream.
export async function readSseStream(
  url: string,
  body: unknown,
  handlers: SseHandlers,
  signal?: AbortSignal,
  options?: SseStreamOptions,
): Promise<void> {
  const firstTokenTimeoutMs = options?.firstTokenTimeoutMs ?? DEFAULT_FIRST_TOKEN_TIMEOUT_MS;
  const idleTimeoutMs = options?.idleTimeoutMs ?? DEFAULT_IDLE_TIMEOUT_MS;

  // Internal controller so a stall aborts the fetch WITHOUT marking the caller's
  // signal as aborted (that distinction drives fallback-vs-give-up downstream).
  const ctl = new AbortController();
  const onExternalAbort = () => ctl.abort();
  if (signal) {
    if (signal.aborted) ctl.abort();
    else signal.addEventListener("abort", onExternalAbort, { once: true });
  }

  let stalled = false;
  let timer: ReturnType<typeof setTimeout> | null = null;
  const clearTimer = () => {
    if (timer) {
      clearTimeout(timer);
      timer = null;
    }
  };
  const armTimer = (ms: number) => {
    clearTimer();
    timer = setTimeout(() => {
      stalled = true;
      ctl.abort();
    }, ms);
  };

  let sawDone = false;
  let streamError: unknown = null;

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify(body),
      cache: "no-store",
      signal: ctl.signal,
    });
    if (!res.ok || !res.body) {
      throw new Error(`sse stream -> ${res.status}`);
    }

    // First-token deadline starts as soon as the response head arrives.
    armTimer(firstTokenTimeoutMs);

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const { frames, rest } = parseFrames(buffer);
      buffer = rest;
      for (const frame of frames) {
        const parsed = safeParse(frame.data);
        switch (frame.event) {
          case "meta":
            handlers.onMeta?.(parsed);
            break;
          case "token":
            // Reset the idle deadline on every token.
            armTimer(idleTimeoutMs);
            handlers.onToken?.(
              typeof parsed === "object" && parsed !== null && "text" in parsed
                ? String((parsed as { text: unknown }).text ?? "")
                : String(parsed),
            );
            break;
          case "done":
            sawDone = true;
            clearTimer();
            handlers.onDone?.(parsed);
            break;
          case "error":
            streamError = parsed;
            clearTimer();
            handlers.onError?.(parsed);
            break;
          default:
            break;
        }
      }
    }
  } catch (err) {
    if (stalled) throw new SseStallError();
    throw err;
  } finally {
    clearTimer();
    if (signal) signal.removeEventListener("abort", onExternalAbort);
  }

  if (streamError !== null) {
    throw new Error(
      typeof streamError === "object" && streamError !== null && "message" in streamError
        ? String((streamError as { message: unknown }).message)
        : "sse stream error",
    );
  }

  // m2: a clean transport close before a terminal `done` (truncated stream) is a
  // failure, not success, so the caller falls back instead of rendering partial
  // or empty prose.
  if (!sawDone) {
    throw new Error("sse stream ended without done");
  }
}
