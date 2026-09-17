import { useLayoutEffect, useState, type RefObject } from "react";
import { readFlexTicks, type FlexTickLayout } from "./flexDeckTicks";

interface Props {
  hostRef: RefObject<HTMLElement | null>;
}

/** A–D left / 1–3 bottom, aligned to official Flex slot-base boxes. A is back/top. */
export function FlexReplayTicks({ hostRef }: Props) {
  const [ticks, setTicks] = useState<FlexTickLayout | null>(null);
  useLayoutEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    let raf = 0;
    const measure = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const next = readFlexTicks(host);
        setTicks((prev) => (JSON.stringify(prev) === JSON.stringify(next) ? prev : next));
      });
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(host);
    const mo = new MutationObserver(measure);
    mo.observe(host, { childList: true, subtree: true });
    window.addEventListener("resize", measure);
    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      mo.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, [hostRef]);
  if (!ticks) return null;
  return (
    <div className="flex-deck-ticks" data-testid="flex-replay-ticks" aria-hidden="true">
      {ticks.rows.map((tick) => (
        <span
          key={`r-${tick.label}`}
          className="flex-deck-tick row"
          data-tick={tick.label}
          style={{ left: tick.x, top: tick.y }}
        >
          {tick.label}
        </span>
      ))}
      {ticks.cols.map((tick) => (
        <span
          key={`c-${tick.label}`}
          className="flex-deck-tick col"
          data-tick={tick.label}
          style={{ left: tick.x, top: tick.y }}
        >
          {tick.label}
        </span>
      ))}
    </div>
  );
}
