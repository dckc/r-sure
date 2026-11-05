import { Link } from "react-router-dom";
import { mapEntries, shortUri, useRead } from "../lib/chain";
import { Panel, Uri } from "../components/ui";

export default function Brokers() {
  const brokers = useRead("broker-book", "brokers");
  return (
    <div className="stack">
      <Panel
        title={<h1>Brokers</h1>}
        actions={<Link className="button" to="/brokers/new">Register broker</Link>}
      >
        <p className="muted">
          A broker is the registered intermediary that opens placing slips. One broker per
          owner address.
        </p>
      </Panel>
      {brokers.isLoading && <Panel><p className="muted">Reading the book…</p></Panel>}
      <div className="grid two">
        {mapEntries<string>(brokers.data).map(([id, uri]) => (
          <div className="card" key={id}>
            <strong>{id}</strong>
            <Uri value={uri} />
            <Link className="button ghost" to={`/brokers/${encodeURIComponent(uri)}`}>
              Open {shortUri(uri)}
            </Link>
          </div>
        ))}
      </div>
      {!brokers.isLoading && mapEntries(brokers.data).length === 0 && (
        <Panel><p className="muted">No brokers registered yet.</p></Panel>
      )}
    </div>
  );
}
