import { Link } from "react-router-dom";
import { mapEntries, shortUri, useRead } from "../lib/chain";
import { Panel, Uri } from "../components/ui";

export default function Claims() {
  const claims = useRead("claim-book", "claims");
  return (
    <div className="stack">
      <Panel title={<h1>Claims</h1>}>
        <p className="muted">
          Claims are notified against a policy, classified, assessed and agreed by the line
          managers, then settled. Settlement pays through the lines and the central fund.
        </p>
      </Panel>
      {claims.isLoading && <Panel><p className="muted">Reading the book…</p></Panel>}
      <div className="grid two">
        {mapEntries<string>(claims.data).map(([id, uri]) => (
          <div className="card" key={id}>
            <strong>{id}</strong>
            <Uri value={uri} />
            <Link className="button ghost" to={`/claims/${encodeURIComponent(uri)}`}>Open {shortUri(uri)}</Link>
          </div>
        ))}
      </div>
      {!claims.isLoading && mapEntries(claims.data).length === 0 && (
        <Panel><p className="muted">No claims notified yet.</p></Panel>
      )}
    </div>
  );
}
