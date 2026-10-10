import {
  Component,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ComponentType,
  type PointerEvent as ReactPointerEvent,
  type ReactNode,
} from "react";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { normalizeAnalysisOutput } from "@visualizer/normalize-analysis";
import ProtocolOperationAnimator from "@visualizer/animator";
import { safeNormalizeAnalysis } from "./analysis";
import { OverlayChrome } from "./OverlayChrome";

const animatorTheme = createTheme({
  palette: {
    primary: { main: "#2563eb" },
    secondary: { main: "#0d9488" },
  },
});

type AnimatorPosition = {
  commandId: string | null;
  fraction: number;
  isPlaying: boolean;
  speed: number;
};

const Animator = ProtocolOperationAnimator as ComponentType<{
  analysisOutput: unknown;
  position?: AnimatorPosition;
  onPositionChange?: (next: AnimatorPosition) => void;
}>;

class AnimatorGuard extends Component<{ children: ReactNode; resetKey: string }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError(): { failed: boolean } {
    return { failed: true };
  }

  componentDidUpdate(prev: { resetKey: string }): void {
    if (prev.resetKey !== this.props.resetKey && this.state.failed) this.setState({ failed: false });
  }

  render() {
    if (this.state.failed) return <p className="file">这个分析结果无法在下半部分播放。</p>;
    return this.props.children;
  }
}
import { spotForTime, stepIndexAt, timeForSpot, type TimelineStep } from "./flex3dTimeline";

type Cam = { az: number; el: number; dist: number };
type CamJson = { azimuth: number; elevation: number; distance: number };
type Step = TimelineStep & {
  index: number;
  cmd: number;
  text: string;
  detail: string;
  slots: string[];
  tool: string | null;
};
type Info = {
  key: string;
  title: string;
  duration: number;
  pipettes: { mount: string; name: string; tool: string }[];
  camera: { main: CamJson & { lookat: number[] }; close: CamJson };
  limits: { elevation: [number, number]; mainDistance: [number, number]; closeDistance: [number, number] };
  frame: { main_width: number; main_height: number; close_width: number; close_height: number; fps: number };
  steps: Step[];
};
type View = { source: "session" | "example"; key: string; note: string; info: Info };
type Which = "main" | "close";

const SPEEDS = [0.5, 1, 2, 4];
// Keep the cameras above the deck. The server also clamps elevation to -89..-1.
const EL_MIN = -85;
const EL_MAX = -2;
const LOST_HINT = "画面暂时断开。再拖动或点播放可重试。";

class RequestError extends Error {
  constructor(
    readonly status: number,
    message: string
  ) {
    super(message);
  }
}

function clamp(value: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, value));
}

function isAbort(err: unknown): boolean {
  return err instanceof DOMException && err.name === "AbortError";
}

function messageOf(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}

function sleep(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(resolve, ms);
    signal.addEventListener(
      "abort",
      () => {
        clearTimeout(timer);
        reject(new DOMException("aborted", "AbortError"));
      },
      { once: true }
    );
  });
}

async function getJson<T>(url: string, signal: AbortSignal): Promise<T> {
  const res = await fetch(url, { signal: AbortSignal.any([signal, AbortSignal.timeout(15000)]) });
  const body = (await res.json().catch(() => ({}))) as Record<string, unknown>;
  if (!res.ok) {
    throw new RequestError(res.status, typeof body.message === "string" ? body.message : `HTTP ${res.status}`);
  }
  return body as T;
}

function blobOf(res: Response): Promise<Blob> {
  if (!res.ok) throw new Error(`画面请求失败（${res.status}）`);
  return res.blob();
}

/** The 3D view for this session, or the example when there is no session. Retries while the servers start. */
async function loadView(sessionId: string | null, signal: AbortSignal): Promise<View> {
  for (let attempt = 0; ; attempt++) {
    try {
      if (sessionId) {
        return await getJson<View>(`/api/session/${encodeURIComponent(sessionId)}/flex3d`, signal);
      }
      const info = await getJson<Info>("/flex3d/example/info", signal);
      return { source: "example", key: "example", note: "没有会话，显示串行稀释示例。", info };
    } catch (err) {
      if (signal.aborted || isAbort(err)) throw err;
      const starting = err instanceof TypeError || (err instanceof RequestError && err.status === 503);
      if (!starting || attempt >= 20) throw err;
      await sleep(500, signal);
    }
  }
}

function defaultCams(meta: Info): Record<Which, Cam> {
  const main = meta.camera.main;
  const close = meta.camera.close;
  return {
    main: { az: main.azimuth, el: main.elevation, dist: main.distance },
    close: { az: close.azimuth, el: close.elevation, dist: close.distance },
  };
}

export function Flex3dOverlay({
  onClose,
  sessionId = null,
  resetKey = "",
}: {
  onClose: () => void;
  /** The chat session whose script the 3D view shows. Null shows the serial dilution example. */
  sessionId?: string | null;
  /** Changes when the session's analysis changes, so the view reloads. */
  resetKey?: string;
}) {
  const [view, setView] = useState<View | null>(null);
  const [analyze, setAnalyze] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");
  const [hint, setHint] = useState("");
  const [t, setT] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);

  const mainWin = useRef<HTMLDivElement>(null);
  const closeWin = useRef<HTMLDivElement>(null);
  const mainImg = useRef<HTMLImageElement>(null);
  const closeImg = useRef<HTMLImageElement>(null);
  const stepList = useRef<HTMLOListElement>(null);

  // Mutable state that requests and the clock read. The React state above only drives the page.
  const meta = useRef<Info | null>(null);
  const key = useRef("");
  const clock = useRef({ t: 0, playing: false, speed: 1, duration: 0 });
  const cams = useRef<Record<Which, Cam>>({
    main: { az: 86.2, el: -40.2, dist: 1.78 },
    close: { az: 62, el: -20, dist: 0.25 },
  });
  const frames = useRef({
    alive: false,
    busy: false,
    again: false,
    gen: 0,
    controller: new AbortController(),
    urls: { main: "", close: "" } as Record<Which, string>,
  });
  const drag = useRef<{ which: Which; x: number; y: number; az: number; el: number } | null>(null);

  // Ask for the frames at the clock's time. Requests do not stack: one runs, and a request made
  // meanwhile runs right after it with the newest time and camera.
  const wake = (): void => {
    const f = frames.current;
    if (!f.alive) return;
    if (f.busy) {
      f.again = true;
      return;
    }
    if (!meta.current || !key.current) return;
    f.busy = true;
    f.again = false;
    const gen = f.gen;
    const time = clock.current.t;
    const url = (which: Which): string => {
      const cam = cams.current[which];
      return (
        `/flex3d/${key.current}/${which}.jpg?t=${time.toFixed(3)}` +
        `&az=${cam.az.toFixed(2)}&el=${cam.el.toFixed(2)}&dist=${cam.dist.toFixed(3)}`
      );
    };
    const signal = AbortSignal.any([f.controller.signal, AbortSignal.timeout(10000)]);
    Promise.all([fetch(url("main"), { signal }).then(blobOf), fetch(url("close"), { signal }).then(blobOf)])
      .then(([mainBlob, closeBlob]) => {
        if (!f.alive || gen !== f.gen) return;
        show(mainImg.current, mainBlob, "main");
        show(closeImg.current, closeBlob, "close");
        setHint("");
      })
      .catch((err: unknown) => {
        if (!f.alive || gen !== f.gen || isAbort(err)) return;
        // Keep the page usable: playback stops where the clock is, and the next action retries.
        clock.current.playing = false;
        setPlaying(false);
        setHint(LOST_HINT);
      })
      .finally(() => {
        f.busy = false;
        if (f.alive && f.again) wake();
      });
  };

  const show = (img: HTMLImageElement | null, blob: Blob, which: Which): void => {
    if (!img) return;
    const next = URL.createObjectURL(blob);
    const previous = frames.current.urls[which];
    frames.current.urls[which] = next;
    img.src = next;
    if (previous) URL.revokeObjectURL(previous);
  };

  const seek = (time: number): void => {
    clock.current.t = clamp(time, 0, clock.current.duration);
    setT(clock.current.t);
    wake();
  };

  const setPlay = (on: boolean): void => {
    const c = clock.current;
    if (on && c.duration <= 0) return;
    if (on && c.t >= c.duration - 0.05) c.t = 0;
    c.playing = on;
    setPlaying(on);
    setT(c.t);
    wake();
  };

  const changeSpeed = (next: number): void => {
    clock.current.speed = next;
    setSpeed(next);
  };

  const resetCams = (): void => {
    if (!meta.current) return;
    cams.current = defaultCams(meta.current);
    wake();
  };

  // One clock while playing: time moves at the chosen speed; the page refreshes about ten times a second.
  useEffect(() => {
    if (!playing) return undefined;
    let raf = 0;
    let last = performance.now();
    let shownAt = last;
    const tick = (now: number): void => {
      const c = clock.current;
      c.t = Math.min(c.duration, c.t + ((now - last) / 1000) * c.speed);
      last = now;
      if (c.t >= c.duration) {
        c.playing = false;
        setPlaying(false);
        setT(c.t);
        wake();
        return;
      }
      if (now - shownAt >= 100) {
        shownAt = now;
        setT(c.t);
        wake();
      }
      raf = window.requestAnimationFrame(tick);
    };
    raf = window.requestAnimationFrame(tick);
    return () => window.cancelAnimationFrame(raf);
  }, [playing]);

  // Load the view for this session (or the example), and the analysis the animator plays.
  useEffect(() => {
    const controller = new AbortController();
    frames.current.gen += 1;
    clock.current = { t: 0, playing: false, speed: clock.current.speed, duration: 0 };
    meta.current = null;
    key.current = "";
    setPlaying(false);
    setView(null);
    setAnalyze(null);
    setError("");
    setHint("");
    setT(0);
    (async () => {
      try {
        const next = await loadView(sessionId, controller.signal);
        const script = await getJson<Record<string, unknown>>(
          `/flex3d/${next.key}/analysis.json`,
          controller.signal
        );
        if (controller.signal.aborted) return;
        meta.current = next.info;
        key.current = next.key;
        cams.current = defaultCams(next.info);
        clock.current = { t: 0, playing: false, speed: clock.current.speed, duration: next.info.duration };
        setView(next);
        setAnalyze(script);
        wake();
      } catch (err) {
        if (controller.signal.aborted || isAbort(err)) return;
        setError(messageOf(err));
      }
    })();
    return () => controller.abort();
  }, [sessionId, resetKey]);

  // Mount: take focus off the 三维 button, keep Space for play/pause, and take wheel zoom on the views.
  useEffect(() => {
    const f = frames.current;
    f.alive = true;
    f.controller = new AbortController();
    (document.activeElement as HTMLElement | null)?.blur?.();

    const onKey = (event: KeyboardEvent): void => {
      if (event.code !== "Space") return;
      // Leave Space to focused text fields and buttons (a button fires its own click).
      // The timeline slider keeps Space as play/pause.
      const el = event.target as HTMLElement | null;
      const tag = el?.tagName;
      const textInput = tag === "INPUT" && (el as HTMLInputElement).type !== "range";
      if (textInput || tag === "TEXTAREA" || tag === "BUTTON" || tag === "SELECT" || el?.isContentEditable) return;
      event.preventDefault();
      if (event.repeat) return;
      setPlay(!clock.current.playing);
    };
    window.addEventListener("keydown", onKey);

    const zoom = (which: Which) => (event: WheelEvent) => {
      const shown = meta.current;
      if (!shown) return;
      event.preventDefault();
      const [lo, hi] = which === "main" ? shown.limits.mainDistance : shown.limits.closeDistance;
      const cam = cams.current[which];
      cam.dist = clamp(cam.dist * Math.exp(event.deltaY * 0.0012), lo, hi);
      wake();
    };
    const onMainWheel = zoom("main");
    const onCloseWheel = zoom("close");
    const main = mainWin.current;
    const close = closeWin.current;
    main?.addEventListener("wheel", onMainWheel, { passive: false });
    close?.addEventListener("wheel", onCloseWheel, { passive: false });

    return () => {
      f.alive = false;
      f.controller.abort();
      window.removeEventListener("keydown", onKey);
      main?.removeEventListener("wheel", onMainWheel);
      close?.removeEventListener("wheel", onCloseWheel);
      for (const url of [f.urls.main, f.urls.close]) {
        if (url) URL.revokeObjectURL(url);
      }
    };
  }, []);

  const pointerDown = (which: Which) => (event: ReactPointerEvent<HTMLDivElement>) => {
    if (!meta.current) return;
    event.currentTarget.setPointerCapture(event.pointerId);
    const cam = cams.current[which];
    drag.current = { which, x: event.clientX, y: event.clientY, az: cam.az, el: cam.el };
    event.currentTarget.style.cursor = "grabbing";
  };
  const pointerMove = (event: ReactPointerEvent<HTMLDivElement>): void => {
    const d = drag.current;
    if (!d) return;
    const cam = cams.current[d.which];
    cam.az = d.az - (event.clientX - d.x) * 0.45;
    cam.el = clamp(d.el + (event.clientY - d.y) * 0.28, EL_MIN, EL_MAX);
    wake();
  };
  const pointerUp = (event: ReactPointerEvent<HTMLDivElement>): void => {
    drag.current = null;
    event.currentTarget.style.cursor = "grab";
  };

  const steps = view?.info.steps ?? [];
  const duration = view?.info.duration ?? 0;
  const currentStep = view ? stepIndexAt(steps, t) : -1;
  const ready = view != null && !error;

  // The bottom animator reads the same analysis the 3D view was built from.
  const analysisOutput = useMemo(
    () =>
      analyze
        ? safeNormalizeAnalysis(
            analyze,
            (input) => normalizeAnalysisOutput(input),
            "Flex"
          )
        : null,
    [analyze]
  );
  const position = useMemo<AnimatorPosition | undefined>(() => {
    if (!view) return undefined;
    const spot = spotForTime(view.info.steps, t);
    return { commandId: spot.commandId, fraction: spot.fraction, isPlaying: playing, speed };
  }, [view, t, playing, speed]);

  // The animator's own controls move the shared clock, and the 3D views follow.
  const onAnimatorPosition = (next: AnimatorPosition): void => {
    const shown = meta.current;
    if (!shown) return;
    changeSpeed(next.speed);
    seek(timeForSpot(shown.steps, next.commandId, next.fraction));
    setPlay(next.isPlaying);
  };

  useEffect(() => {
    if (!playing || currentStep < 0) return;
    stepList.current
      ?.querySelector<HTMLElement>(`[data-index="${currentStep}"]`)
      ?.scrollIntoView({ block: "nearest" });
  }, [currentStep, playing]);

  const label = view
    ? view.source === "session"
      ? `会话脚本：${view.info.title}`
      : view.note || `示例：${view.info.title}`
    : "";

  return (
    <OverlayChrome onClose={onClose}>
      <div className="flex3d">
        <div className="flex3d-top">
          <div className="flex3d-bar">
            <button type="button" className="ghost" disabled={!ready} onClick={() => setPlay(!playing)}>
              {playing ? "暂停" : "播放"}
            </button>
            <input
              type="range"
              min={0}
              max={duration || 0}
              step={0.05}
              value={Math.min(t, duration)}
              disabled={!ready}
              aria-label="时间"
              onChange={(event) => seek(Number(event.target.value))}
            />
            <span className="flex3d-time">
              {t.toFixed(1)} / {duration.toFixed(1)} s
            </span>
            <select
              className="flex3d-speed"
              aria-label="速度"
              value={speed}
              disabled={!ready}
              onChange={(event) => changeSpeed(Number(event.target.value))}
            >
              {SPEEDS.map((value) => (
                <option key={value} value={value}>
                  {value}×
                </option>
              ))}
            </select>
            <button type="button" className="ghost" disabled={!ready} onClick={resetCams}>
              重置视角
            </button>
          </div>
          <div className="flex3d-grid">
            <div
              className="flex3d-win flex3d-main"
              ref={mainWin}
              onPointerDown={pointerDown("main")}
              onPointerMove={pointerMove}
              onPointerUp={pointerUp}
              onPointerCancel={pointerUp}
            >
              <img ref={mainImg} alt="主视角" draggable={false} />
              <span className="flex3d-tag">主视角 · 拖动转动，滚轮缩放</span>
            </div>
            <div
              className="flex3d-win flex3d-close"
              ref={closeWin}
              onPointerDown={pointerDown("close")}
              onPointerMove={pointerMove}
              onPointerUp={pointerUp}
              onPointerCancel={pointerUp}
            >
              <img ref={closeImg} alt="跟随特写" draggable={false} />
              <span className="flex3d-tag">跟随特写 · 拖动转动，滚轮缩放</span>
            </div>
            <div className="flex3d-win flex3d-steps-win">
              <ol className="flex3d-steps" ref={stepList}>
                {steps.map((step) => (
                  <li
                    key={step.index}
                    data-index={step.index}
                    className={step.index === currentStep ? "active" : undefined}
                  >
                    <button type="button" onClick={() => seek(step.t0)}>
                      <span className="flex3d-step-time">{step.t0.toFixed(1)} s</span>
                      <span>{step.text}</span>
                    </button>
                  </li>
                ))}
              </ol>
            </div>
          </div>
          {!ready ? <p className="flex3d-msg">{error || "正在准备三维…"}</p> : null}
        </div>
        <div className="flex3d-bottom">
          {analyze && analysisOutput && view ? (
            <ThemeProvider theme={animatorTheme}>
              <AnimatorGuard resetKey={view.key}>
                <Animator
                  analysisOutput={analysisOutput}
                  position={position}
                  onPositionChange={onAnimatorPosition}
                />
              </AnimatorGuard>
            </ThemeProvider>
          ) : analyze ? (
            <p className="file">这个分析结果无法在下半部分播放。</p>
          ) : error ? null : (
            <p className="file">正在准备动画…</p>
          )}
        </div>
        <p className="flex3d-note">{hint || label}</p>
      </div>
    </OverlayChrome>
  );
}

export default Flex3dOverlay;
