import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import DeployResult from "../components/DeployResult";
import EntityHeader from "../components/EntityHeader";
import { Field, Json, Panel } from "../components/ui";
import { policyRole } from "../lib/capabilities";
import { useUriRead } from "../lib/chain";
import { useWallet } from "../lib/store";
import type { PolicyState, State } from "../lib/types";
import { useAction } from "../lib/useAction";

export default function Policy() {
  const { uri } = useParams<{ uri: string }>();
  const decoded = uri ? decodeURIComponent(uri) : "";
  const { client, address } = useWallet();
  const info = useUriRead<PolicyState>(decoded, "info");
  const terms = useUriRead(decoded, "terms");
  const lines = useUriRead(decoded, "lines");
  const claims = useUriRead(decoded, "claims");
  const action = useAction("policy", decoded);
  const [lossHeight, setLossHeight] = useState("0");
  const [amount, setAmount] = useState("1000");
  const [evidence, setEvidence] = useState("loss");

  if (!decoded) return <Panel><p className="error">Missing policy URI.</p></Panel>;
  if (info.isLoading) return <Panel><p className="muted">Reading policy…</p></Panel>;
  if (info.error) return <Panel><p className="error">{String(info.error)}</p></Panel>;
  const entity = info.data ?? {};
  const role = policyRole(entity, address);
  const write = (summary: string, arm: string, args: unknown[], ownerFirst = true) =>
    action.run(summary, () => client!.write_uri_json(decoded, arm, JSON.stringify(args), ownerFirst), [["read-uri", decoded]]);

  const openClaim = () => {
    const req = {
      lossHeight: Number(lossHeight),
      claimedAmount: Number(amount),
      evidence: [{ kind: "loss", hash: evidence }],
    };
    void write("open claim", "openClaim", [req]);
  };

  return (
    <div className="stack">
      <Panel>
        <EntityHeader
          kind="policies"
          uri={decoded}
          title={String(entity.id ?? "Policy")}
          status={String(entity.status ?? "active")}
          actions={<span className="pill">{role.allowed ? role.reason : "read-only"}</span>}
        />
        <div className="grid two">
          <div className="stat"><span className="muted">Aggregate</span><strong>{String(entity.aggregateLimit ?? "—")}</strong></div>
          <div className="stat"><span className="muted">Remaining</span><strong>{String(entity.aggregateRemaining ?? "—")}</strong></div>
          <div className="stat"><span className="muted">Per claim</span><strong>{String(entity.perClaimLimit ?? "—")}</strong></div>
          <div className="stat"><span className="muted">Deductible</span><strong>{String(entity.deductible ?? "—")}</strong></div>
        </div>
        {!role.allowed && <p className="muted">{role.reason}.</p>}
      </Panel>

      <Panel title={<h2>Notify a claim</h2>}>
        <div className="grid two">
          <Field label="Loss height"><input value={lossHeight} onChange={(e) => setLossHeight(e.target.value)} inputMode="numeric" /></Field>
          <Field label="Claimed amount"><input value={amount} onChange={(e) => setAmount(e.target.value)} inputMode="numeric" /></Field>
          <Field label="Evidence hash"><input value={evidence} onChange={(e) => setEvidence(e.target.value)} /></Field>
        </div>
        <button className="button" disabled={!role.allowed || action.busy} onClick={openClaim}>Open claim</button>
        <DeployResult busy={action.busy} error={action.error} refusal={action.refusal} receipt={action.receipt} />
      </Panel>

      <Panel
        title={<h2>Expiry</h2>}
        actions={<button className="button ghost" disabled={action.busy} onClick={() => void write("expire policy", "expire", [], false)}>Expire</button>}
      >
        <p className="muted">Expiry releases every line; it is permissionless once the run-off period has passed.</p>
      </Panel>

      <Panel title={<h2>Lines</h2>}><Json value={lines.data ?? []} /></Panel>
      <Panel title={<h2>Claims</h2>}>
        {Object.entries((claims.data ?? {}) as Record<string, State>).map(([id, claim]) => (
          <div className="row spread" key={id}>
            <span>{id}</span>
            <span className="pill">{String(claim.status ?? "unknown")}</span>
            <Link to={`/claims/${encodeURIComponent(String(claim.uri ?? ""))}`}>open</Link>
          </div>
        ))}
      </Panel>
      <Panel title={<h2>Terms</h2>}><Json value={terms.data ?? {}} /></Panel>
      <Panel title={<h2>Raw state</h2>}><Json value={entity} /></Panel>
    </div>
  );
}
