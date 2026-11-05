import { useState } from "react";
import { useParams } from "react-router-dom";
import DeployResult from "../components/DeployResult";
import EntityHeader from "../components/EntityHeader";
import { Field, Json, Panel } from "../components/ui";
import { claimManager } from "../lib/capabilities";
import { useUriRead } from "../lib/chain";
import { useWallet } from "../lib/store";
import type { ClaimState } from "../lib/types";
import { useAction } from "../lib/useAction";

export default function Claim() {
  const { uri } = useParams<{ uri: string }>();
  const decoded = uri ? decodeURIComponent(uri) : "";
  const { client, address } = useWallet();
  const info = useUriRead<ClaimState>(decoded, "info");
  const evidence = useUriRead(decoded, "evidence");
  const action = useAction("claim", decoded);
  const [kind, setKind] = useState("standard");
  const [recommended, setRecommended] = useState("1000");
  const [agreed, setAgreed] = useState("1000");
  const [basis, setBasis] = useState("assessment");
  const [dispute, setDispute] = useState("{}");
  const [newEvidence, setNewEvidence] = useState("{}");

  if (!decoded) return <Panel><p className="error">Missing claim URI.</p></Panel>;
  if (info.isLoading) return <Panel><p className="muted">Reading claim…</p></Panel>;
  if (info.error) return <Panel><p className="error">{String(info.error)}</p></Panel>;
  const entity = info.data ?? {};
  const manager = claimManager(entity, address);
  const write = (summary: string, arm: string, args: unknown[], ownerFirst = true) =>
    action.run(summary, () => client!.write_uri_json(decoded, arm, JSON.stringify(args), ownerFirst), [["read-uri", decoded]]);

  return (
    <div className="stack">
      <Panel>
        <EntityHeader
          kind="claims"
          uri={decoded}
          title={String(entity.id ?? "Claim")}
          status={String(entity.status ?? "notified")}
          actions={<span className="pill">{manager.allowed ? manager.reason : "read-only"}</span>}
        />
        <div className="grid two">
          <div className="stat"><span className="muted">Claimed</span><strong>{String(entity.claimedAmount ?? "—")}</strong></div>
          <div className="stat"><span className="muted">Agreed</span><strong>{String(entity.agreedAmount ?? "—")}</strong></div>
          <div className="stat"><span className="muted">Paid</span><strong>{String(entity.paid ?? "—")}</strong></div>
          <div className="stat"><span className="muted">Loss height</span><strong>{String(entity.lossHeight ?? "—")}</strong></div>
        </div>
        {!manager.allowed && <p className="muted">{manager.reason}.</p>}
      </Panel>

      <Panel title={<h2>Classification and assessment</h2>}>
        <div className="grid two">
          <Field label="Class">
            <select value={kind} onChange={(e) => setKind(e.target.value)}>
              <option value="standard">standard</option>
              <option value="complex">complex</option>
            </select>
          </Field>
          <Field label="Recommended amount"><input value={recommended} onChange={(e) => setRecommended(e.target.value)} inputMode="numeric" /></Field>
        </div>
        <div className="row gap">
          <button className="button" disabled={!manager.allowed} onClick={() => void write("classify claim", "classify", [kind])}>Classify</button>
          <button className="button" disabled={!manager.allowed} onClick={() => void write("assess claim", "assess", [{ recommendedAmount: Number(recommended), basisHash: "assessment" }])}>Assess</button>
        </div>
        <DeployResult busy={action.busy} error={action.error} refusal={action.refusal} receipt={action.receipt} />
      </Panel>

      <Panel title={<h2>Agreement</h2>}>
        <div className="grid two">
          <Field label="Agreed amount"><input value={agreed} onChange={(e) => setAgreed(e.target.value)} inputMode="numeric" /></Field>
          <Field label="Basis hash"><input value={basis} onChange={(e) => setBasis(e.target.value)} /></Field>
        </div>
        <button className="button" disabled={!manager.allowed} onClick={() => void write("agree claim", "agree", [Number(agreed), basis])}>Agree</button>
      </Panel>

      <Panel title={<h2>Dispute and settle</h2>}>
        <Field label="Case request JSON"><textarea value={dispute} onChange={(e) => setDispute(e.target.value)} /></Field>
        <button className="button ghost" disabled={!manager.allowed} onClick={() => void write("dispute claim", "dispute", [JSON.parse(dispute)])}>Dispute</button>
        <div className="row gap">
          <button className="button" onClick={() => void write("settle claim", "settle", [], false)}>Settle</button>
          <button className="button ghost" onClick={() => void write("close claim", "close", [], false)}>Close</button>
        </div>
      </Panel>

      <Panel title={<h2>Evidence</h2>}>
        <Field label="Evidence item JSON"><textarea value={newEvidence} onChange={(e) => setNewEvidence(e.target.value)} /></Field>
        <button className="button ghost" disabled={!manager.allowed} onClick={() => void write("add evidence", "addEvidence", [[JSON.parse(newEvidence)]])}>Add evidence</button>
        <Json value={evidence.data ?? []} />
      </Panel>
      <Panel title={<h2>Raw state</h2>}><Json value={entity} /></Panel>
    </div>
  );
}
