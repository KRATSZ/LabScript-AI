import type { ArchivedThread } from "./threadArchive";

interface Props {
  threads: ArchivedThread[];
  currentId?: string | null;
  open: boolean;
  onToggle: () => void;
  onSelect: (id: string) => void;
}

export function HistoryRail({ threads, currentId, open, onToggle, onSelect }: Props) {
  const present = Boolean(threads.length || currentId);
  const classes = ["history-rail"];
  if (present) classes.push("present");
  if (present && open) classes.push("open");
  return (
    <aside className={classes.join(" ")} data-testid="history-rail" aria-label="History">
      {present ? (
        <button
          type="button"
          className="history-rail-toggle"
          aria-expanded={open}
          onClick={onToggle}
          title={open ? "Hide runs" : "Show runs"}
        >
          History
        </button>
      ) : null}
      {present && open ? (
        <ol className="history-rail-list">
          {threads.map((thread) => (
            <li key={thread.id}>
              <button
                type="button"
                className={thread.id === currentId ? "history-rail-item current" : "history-rail-item"}
                onClick={() => onSelect(thread.id)}
              >
                <span className="history-rail-title">{thread.title}</span>
              </button>
            </li>
          ))}
        </ol>
      ) : null}
    </aside>
  );
}
