import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { loadCatalogue } from "../lib/catalogue";
import { asMap, shortUri, useRead } from "../lib/chain";
import { useWallet } from "../lib/store";
import { Panel, StatusPill, Uri } from "../components/ui";

export default function Overview() {
  const { client, node, address, readiness } = useWallet();
  const paused = useRead<boolean>("admin", "isPaused");
  const syndicates = useRead("syndicate-book", "syndicates");
  const risks = useRead("risk-book", "risks");
  const policies = useRead("policy-book", "policies");
  const claims = useRead("claim-book", "claims");
  const catalogue = useQuery({
    queryKey: ["catalogue"],
    queryFn: () => loadCatalogue(undefined, readiness.root),
    staleTime: 30_000,
  });

  const counts = [
    ["Syndicates", syndicates.data ? Object.keys(asMap(syndicates.data)).length : "…"],
    ["Risks", risks.data ? Object.keys(asMap(risks.data)).length : "…"],
    ["Policies", policies.data ? Object.keys(asMap(policies.data)).length : "…"],
    ["Claims", claims.data ? Object.keys(asMap(claims.data)).length : "…"],
  ];

  return (
    <div className="stack">
      <Panel title={<h1>Overview</h1>}>
        <p className="muted">
          Devnet-only insurance placement. One wallet can act as insured, broker, syndicate
          manager and admin; pages enable only the actions your address may take.
        </p>
        <div className="grid two">
          {counts.map(([label, value]) => (
            <div className="stat" key={label}>
              <span className="muted">{label}</span>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
        <div className="row gap wrap">
          <StatusPill status={paused.data ? "paused" : "active"} />
          <span className="muted">
            {node} · {readiness.shard ?? "?"} · height {client ? "live" : "—"}
          </span>
          {address && <span className="mono small">{shortUri(address)}</span>}
        </div>
      </Panel>

      <Panel title={<h2>Market</h2>}>
        <div className="grid two">
          <Link className="card" to="/syndicates">
            <strong>Syndicates</strong>
            <p>Capacity, quotes, lines and members.</p>
          </Link>
          <Link className="card" to="/brokers">
            <strong>Brokers</strong>
            <p>Registered intermediaries and their slips.</p>
          </Link>
          <Link className="card" to="/risks">
            <strong>Risks</strong>
            <p>Submit, assess and accept an insured risk.</p>
          </Link>
          <Link className="card" to="/slips">
            <strong>Slips</strong>
            <p>Place, subscribe, accept, fund and bind.</p>
          </Link>
          <Link className="card" to="/policies">
            <strong>Policies</strong>
            <p>Lines, premium, aggregate and claims.</p>
          </Link>
          <Link className="card" to="/claims">
            <strong>Claims</strong>
            <p>Notify, assess, agree, dispute and settle.</p>
          </Link>
        </div>
      </Panel>

      <Panel title={<h2>Curated catalogue</h2>}>
        {catalogue.isLoading && <p className="muted">Loading catalogue…</p>}
        {catalogue.error && <p className="error">{String(catalogue.error)}</p>}
        {!catalogue.isLoading && (catalogue.data?.length ?? 0) === 0 && (
          <p className="muted">
            No catalogue. Install the contracts, or seed demo data with{" "}
            <code>make web-seed</code>.
          </p>
        )}
        <div className="grid two">
          {catalogue.data?.map((entry) => (
            <div className="card" key={`${entry.kind}:${entry.uri}`}>
              <div className="row spread">
                <strong>{entry.label || shortUri(entry.uri)}</strong>
                <StatusPill status={entry.kind} />
              </div>
              <Uri value={entry.uri} kind={entry.kind} />
            </div>
          ))}
        </div>
      </Panel>
    </div>
  );
}
