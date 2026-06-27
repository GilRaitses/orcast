"use client";

import {
  useCallback,
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

// Single collision-aware tooltip primitive (HANDOFF_CHARTER B7). Fixes the
// real bug where a link inside a tooltip in the lower third of the screen is
// unreachable:
//   (a) collision-aware: flips above/below by available viewport space;
//   (b) hover safe-bridge: a close delay lets the pointer travel into the tip
//       so an interactive link stays clickable;
//   (c) dismiss on Escape / outside-click / blur for interactive content.

interface TooltipProps {
  content: ReactNode;
  children: ReactNode;
  interactive?: boolean;
}

const CLOSE_DELAY_MS = 180;

export default function Tooltip({ content, children, interactive = false }: TooltipProps) {
  const [open, setOpen] = useState(false);
  const [placement, setPlacement] = useState<"top" | "bottom">("top");
  const [coords, setCoords] = useState<{ left: number; top: number }>({ left: 0, top: 0 });
  const triggerRef = useRef<HTMLSpanElement | null>(null);
  const tipRef = useRef<HTMLDivElement | null>(null);
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const tipId = useId();

  const clearClose = useCallback(() => {
    if (closeTimer.current) {
      clearTimeout(closeTimer.current);
      closeTimer.current = null;
    }
  }, []);

  const scheduleClose = useCallback(() => {
    clearClose();
    closeTimer.current = setTimeout(() => setOpen(false), CLOSE_DELAY_MS);
  }, [clearClose]);

  const openNow = useCallback(() => {
    clearClose();
    setOpen(true);
  }, [clearClose]);

  // Position + collision flip. If there is not enough space above, flip below.
  useLayoutEffect(() => {
    if (!open || !triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    const tipHeight = tipRef.current?.offsetHeight ?? 120;
    const tipWidth = tipRef.current?.offsetWidth ?? 220;
    const spaceAbove = rect.top;
    const spaceBelow = window.innerHeight - rect.bottom;
    const place: "top" | "bottom" =
      spaceAbove < tipHeight + 12 && spaceBelow > spaceAbove ? "bottom" : "top";
    setPlacement(place);
    let left = rect.left + rect.width / 2 - tipWidth / 2;
    left = Math.max(8, Math.min(left, window.innerWidth - tipWidth - 8));
    const top = place === "top" ? rect.top - tipHeight - 8 : rect.bottom + 8;
    setCoords({ left, top });
  }, [open, content]);

  // Escape + outside-click dismissal for interactive tooltips.
  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    function onDown(e: MouseEvent) {
      const t = e.target as Node;
      if (
        triggerRef.current?.contains(t) ||
        tipRef.current?.contains(t)
      ) {
        return;
      }
      setOpen(false);
    }
    document.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onDown);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onDown);
    };
  }, [open]);

  useEffect(() => () => clearClose(), [clearClose]);

  return (
    <span
      ref={triggerRef}
      className="tooltip-trigger"
      onMouseEnter={openNow}
      onMouseLeave={scheduleClose}
      onFocus={openNow}
      onBlur={scheduleClose}
      aria-describedby={open ? tipId : undefined}
      tabIndex={0}
    >
      {children}
      {open && (
        <div
          ref={tipRef}
          id={tipId}
          role="tooltip"
          className={`tooltip-pop tooltip-${placement}`}
          style={{ left: coords.left, top: coords.top, position: "fixed" }}
          onMouseEnter={interactive ? openNow : undefined}
          onMouseLeave={interactive ? scheduleClose : undefined}
        >
          {content}
        </div>
      )}
    </span>
  );
}
