"use client";

import { useCallback, useEffect, useRef, useState } from "react";

// Frosted, semi-transparent circular magnifier pinned to the upper-left of the
// 3D viewer. It floats OVER the scene as an overlay and never reflows the
// canvas: the root is absolutely positioned with pointer-events disabled, and
// only the affordance shell re-enables pointer events, so the rest of the
// viewport stays interactive.
//
// State machine (self-contained, see toggle / hover / idle handlers below):
//   - hover-in  : pointer enters the shell -> expand (search field slides out).
//   - icon click: toggles expanded; a click while expanded collapses it.
//   - idle      : after idleCollapseMs with no interaction -> collapse.
// Any interaction (pointer move over the shell, typing, focus, submit) re-arms
// the idle timer so the field stays open while the user is engaged.

export interface SearchAffordanceProps {
  // Emitted when the user submits a non-empty place query (Enter or submit).
  onSearch: (query: string) => void;
  // Idle window (ms) with no interaction before the field auto-collapses.
  idleCollapseMs?: number;
  // Placeholder copy for the place query input.
  placeholder?: string;
}

// Scoped style block. Class names are prefixed `osa-` (orcast search affordance)
// so they cannot collide with the global classes in globals.css. Frosted glass
// matches the dark Salish palette (surface ~#0c1824, text #e6edf3, accent
// #4fb8d8) used across web/app/components/scene/.
const STYLE = `
.osa-root {
  position: absolute;
  top: 14px;
  left: 14px;
  z-index: 6;
  pointer-events: none;
}
.osa-shell {
  display: inline-flex;
  align-items: center;
  pointer-events: auto;
  border-radius: 999px;
  background: rgba(12, 24, 36, 0.42);
  -webkit-backdrop-filter: blur(14px) saturate(150%);
  backdrop-filter: blur(14px) saturate(150%);
  border: 1px solid rgba(230, 237, 243, 0.18);
  box-shadow: 0 6px 22px rgba(0, 0, 0, 0.35);
  overflow: hidden;
  transition: border-color 0.25s ease, box-shadow 0.25s ease, background 0.25s ease;
}
.osa-shell[data-expanded="true"] {
  background: rgba(12, 24, 36, 0.55);
  border-color: rgba(79, 184, 216, 0.55);
  box-shadow: 0 8px 26px rgba(0, 0, 0, 0.45);
}
.osa-btn {
  flex: 0 0 auto;
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  background: transparent;
  border: none;
  cursor: pointer;
  color: #e6edf3;
  padding: 0;
}
.osa-btn:focus-visible {
  outline: 2px solid rgba(79, 184, 216, 0.8);
  outline-offset: -2px;
  border-radius: 999px;
}
.osa-icon {
  width: 20px;
  height: 20px;
  display: block;
}
.osa-field {
  overflow: hidden;
  max-width: 0;
  opacity: 0;
  transition: max-width 0.3s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.22s ease;
}
.osa-shell[data-expanded="true"] .osa-field {
  max-width: 248px;
  opacity: 1;
}
.osa-input {
  width: 216px;
  background: transparent;
  border: none;
  outline: none;
  color: #e6edf3;
  font: inherit;
  font-size: 0.9rem;
  padding: 0 0.85rem 0 0.2rem;
  line-height: 44px;
}
.osa-input::placeholder {
  color: rgba(230, 237, 243, 0.55);
}
`;

export default function SearchAffordance({
  onSearch,
  idleCollapseMs = 4000,
  placeholder = "Search a place…",
}: SearchAffordanceProps) {
  const [expanded, setExpanded] = useState(false);
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement | null>(null);
  const idleTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearIdle = useCallback(() => {
    if (idleTimer.current) {
      clearTimeout(idleTimer.current);
      idleTimer.current = null;
    }
  }, []);

  // Restart the idle countdown. Called on every interaction while open.
  const armIdle = useCallback(() => {
    clearIdle();
    idleTimer.current = setTimeout(() => setExpanded(false), idleCollapseMs);
  }, [clearIdle, idleCollapseMs]);

  // When the field opens, focus the input and start the idle timer; when it
  // closes, stop the timer. Cleanup clears any pending timer on unmount.
  useEffect(() => {
    if (expanded) {
      inputRef.current?.focus();
      armIdle();
    } else {
      clearIdle();
    }
    return clearIdle;
  }, [expanded, armIdle, clearIdle]);

  // Re-arm the idle timer only while open (no-op when collapsed).
  const bumpIdle = useCallback(() => {
    if (expanded) armIdle();
  }, [expanded, armIdle]);

  const submit = useCallback(() => {
    const q = query.trim();
    if (q.length === 0) return;
    onSearch(q);
    bumpIdle();
  }, [query, onSearch, bumpIdle]);

  return (
    <div className="osa-root">
      <style>{STYLE}</style>
      <div
        className="osa-shell"
        data-expanded={expanded}
        onMouseEnter={() => setExpanded(true)}
        onMouseMove={bumpIdle}
      >
        <button
          type="button"
          className="osa-btn"
          aria-label={expanded ? "Collapse place search" : "Open place search"}
          aria-expanded={expanded}
          onClick={(e) => {
            e.stopPropagation();
            setExpanded((v) => !v);
          }}
        >
          <svg
            className="osa-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <circle cx="11" cy="11" r="7" />
            <line x1="21" y1="21" x2="16.5" y2="16.5" />
          </svg>
        </button>
        <form
          className="osa-field"
          onSubmit={(e) => {
            e.preventDefault();
            submit();
          }}
        >
          <input
            ref={inputRef}
            className="osa-input"
            type="text"
            value={query}
            placeholder={placeholder}
            aria-label="Place query"
            tabIndex={expanded ? 0 : -1}
            onChange={(e) => {
              setQuery(e.target.value);
              bumpIdle();
            }}
            onFocus={bumpIdle}
            onKeyDown={(e) => {
              if (e.key === "Escape") {
                setExpanded(false);
              }
            }}
          />
        </form>
      </div>
    </div>
  );
}

// Local default-args sanity check (throwaway story; not wired into any route).
// Confirms the component mounts with only the required prop. Kept as a typed
// reference so the orchestrator can eyeball default behavior at the W1 gate.
export function __SearchAffordanceStory() {
  return <SearchAffordance onSearch={(q) => console.log("search:", q)} />;
}
