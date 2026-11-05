import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { loadCatalogue } from "../lib/catalogue";
import { shortUri } from "../lib/chain";
import { useWallet } from "../lib/store";
import { Panel, Uri } from "../components/ui";

export default function Slips() {
  const readiness = useWallet((state) => state.readiness);
  const catalogue = useQuery({
    queryKey: ["catalogue"],
    queryFn: () => loadCatalogue(undefined, readiness.root),
    staleTime: 30_000,
  });
  const slips = (catalogue.data ?? []).filter((entry) => entry.kind === "slip");

  return (
    <div className="stack">
      <Panel
        title={<h1>Slips</h1>}
        actions={<Link className="button" to="/slips/new">Open slip</Link>}
      >
        <p className="muted">
          There is no global slip book. Slips are discovered through the curated catalogue,
          a broker's slip index, the risk's slip link, or a shared URI.
        </p>
      </Panel>
      {slips.length === 0 ? (
        <Panel><p className="muted">No slips in the catalogue. Open one from an accepted risk.</p></Panel>
      ) : (
        <div className="grid two">
          {slips.map((entry) => (
            <div className="card" key={entry.uri}>
              <strong>{entry.label || shortUri(entry.uri)}</strong>
              <Uri value={entry.uri} />
              <Link className="button ghost" to={`/slips/${encodeURIComponent(entry.uri)}`}>Open</Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
