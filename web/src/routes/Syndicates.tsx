import { Link } from "react-router-dom";
import { mapEntries, shortUri, useRead } from "../lib/chain";
import { Panel, StatusPill, Uri } from "../components/ui";

export default function Syndicates() {
  const syndicates = useRead("syndicate-book", "syndicates");
  const count = useRead<number>("syndicate-book", "count");

  return (
    <div className="stack">
      <Panel
        title={<h1>Syndicates</h1>}
        actions={<Link className="button" to="/syndicates/new">Create syndicate</Link>}
      >
        <p className="muted">
          Capacity is real on-chain capital. A quote reserves capacity until the slip binds
          or the quote expires.
        </p>
        <div className="row gap wrap">
          <span className="pill">count {count.data ?? "…"}</span>
        </div>
      </Panel>

      {syndicates.isLoading && <Panel><p className="muted">Reading the book…</p></Panel>}
      {syndicates.error && <Panel><p className="error">{String(syndicates.error)}</p></Panel>}
      <div className="grid two">
        {mapEntries<string>(syndicates.data).map(([id, uri]) => (
          <div className="card" key={id}>
            <div className="row spread">
              <strong>{id}</strong>
              <StatusPill status="active" />
            </div>
            <Uri value={uri} />
            <Link className="button ghost" to={`/syndicates/${encodeURIComponent(uri)}`}>
              Open {shortUri(uri)}
            </Link>
          </div>
        ))}
      </div>
      {!syndicates.isLoading && mapEntries(syndicates.data).length === 0 && (
        <Panel><p className="muted">No syndicates registered yet.</p></Panel>
      )}
    </div>
  );
}
