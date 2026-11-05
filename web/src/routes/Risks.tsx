import { Link } from "react-router-dom";
import { mapEntries, shortUri, useRead } from "../lib/chain";
import { Panel, Uri } from "../components/ui";

export default function Risks() {
  const risks = useRead("risk-book", "risks");
  return (
    <div className="stack">
      <Panel title={<h1>Risks</h1>} actions={<Link className="button" to="/risks/new">Submit risk</Link>}>
        <p className="muted">
          A risk is the insured's submission. It carries the asset reference, the three
          insurability answers and evidence; the binding terms live on the slip.
        </p>
      </Panel>
      {risks.isLoading && <Panel><p className="muted">Reading the book…</p></Panel>}
      <div className="grid two">
        {mapEntries<string>(risks.data).map(([id, uri]) => (
          <div className="card" key={id}>
            <strong>{id}</strong>
            <Uri value={uri} />
            <Link className="button ghost" to={`/risks/${encodeURIComponent(uri)}`}>Open {shortUri(uri)}</Link>
          </div>
        ))}
      </div>
      {!risks.isLoading && mapEntries(risks.data).length === 0 && (
        <Panel><p className="muted">No risks submitted yet.</p></Panel>
      )}
    </div>
  );
}
