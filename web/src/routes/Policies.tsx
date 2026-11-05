import { Link } from "react-router-dom";
import { mapEntries, shortUri, useRead } from "../lib/chain";
import { Panel, Uri } from "../components/ui";

export default function Policies() {
  const policies = useRead("policy-book", "policies");
  return (
    <div className="stack">
      <Panel title={<h1>Policies</h1>}>
        <p className="muted">
          A policy is a bound slip. It owns the lines, premium, aggregate limit and claims.
        </p>
      </Panel>
      {policies.isLoading && <Panel><p className="muted">Reading the book…</p></Panel>}
      <div className="grid two">
        {mapEntries<string>(policies.data).map(([id, uri]) => (
          <div className="card" key={id}>
            <strong>{id}</strong>
            <Uri value={uri} />
            <Link className="button ghost" to={`/policies/${encodeURIComponent(uri)}`}>Open {shortUri(uri)}</Link>
          </div>
        ))}
      </div>
      {!policies.isLoading && mapEntries(policies.data).length === 0 && (
        <Panel><p className="muted">No policies bound yet.</p></Panel>
      )}
    </div>
  );
}
