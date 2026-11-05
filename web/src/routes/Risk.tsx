import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import DeployResult from "../components/DeployResult";
import EntityHeader from "../components/EntityHeader";
import { Field, Json, Panel } from "../components/ui";
import { riskRole } from "../lib/capabilities";
import { useUriRead } from "../lib/chain";
import { useWallet } from "../lib/store";
import type { RiskState } from "../lib/types";
import { useAction } from "../lib/useAction";

export default function Risk() {
  const { uri } = useParams<{ uri: string }>();
  const decoded = uri ? decodeURIComponent(uri) : "";
  const { client, address } = useWallet();
  const info = useUriRead<RiskState>(decoded, "info");
  const evidence = useUriRead(decoded, "evidence");
  const action = useAction("risk", decoded);
  const [premium, setPremium] = useState("1000");
  const [reason, setReason] = useState("");

  if (!decoded) return <Panel><p className="error">Missing risk URI.</p></Panel>;
  if (info.isLoading) return <Panel><p className="muted">Reading risk…</p></Panel>;
  if (info.error) return <Panel><p className="error">{String(info.error)}</p></Panel>;
  const entity = info.data ?? {};
  const role = riskRole(entity, address);
  const write = (summary: string, arm: string, args: unknown[], ownerFirst = true) =>
    action.run(summary, () => client!.write_uri_json(decoded, arm, JSON.stringify(args), ownerFirst), [["read-uri", decoded]]);

  return (
    <div className="stack">
      <Panel>
        <EntityHeader
          kind="risks"
          uri={decoded}
          title={String(entity.id ?? "Risk")}
          status={String(entity.status ?? "submitted")}
          actions={<span className="pill">{role.allowed ? role.reason : "read-only"}</span>}
        />
        <div className="grid two">
          <div className="stat"><span className="muted">Class</span><strong>{String(entity.class ?? "—")}</strong></div>
          <div className="stat"><span className="muted">Declared value</span><strong>{String(entity.declaredValue ?? "—")}</strong></div>
          <div className="stat"><span className="muted">Requested limit</span><strong>{String(entity.requestedLimit ?? "—")}</strong></div>
          <div className="stat"><span className="muted">Deductible</span><strong>{String(entity.requestedDeductible ?? "—")}</strong></div>
        </div>
        {!role.allowed && <p className="muted">{role.reason}.</p>}
        <Link
          className="button ghost"
          to={`/slips/new?${new URLSearchParams({
            riskId: String(entity.id ?? ""),
            riskUri: decoded,
            class: String(entity.class ?? "property"),
            start: String(entity.periodStart ?? 0),
            end: String(entity.periodEnd ?? 1000000),
          }).toString()}`}
        >
          Open slip from this risk
        </Link>
      </Panel>
      <Panel title={<h2>Assessment</h2>}>
        <div className="row gap">
          <input value={premium} onChange={(e) => setPremium(e.target.value)} inputMode="numeric" />
          <button className="button" disabled={!role.allowed} onClick={() => void write("assess risk", "assess", [{ quotedPremium: Number(premium) }])}>Assess</button>
        </div>
      </Panel>
      <Panel
        title={<h2>Decision</h2>}
        actions={
          <>
            <button className="button" disabled={!role.allowed} onClick={() => void write("accept risk", "accept", [])}>Accept</button>
            <button className="button ghost" disabled={!role.allowed} onClick={() => void write("expire risk", "expire", [], false)}>Expire</button>
          </>
        }
      >
        <div className="row gap">
          <Field label="Decline reason hash"><input value={reason} onChange={(e) => setReason(e.target.value)} /></Field>
          <button className="button ghost" disabled={!role.allowed || !reason} onClick={() => void write("decline risk", "decline", [reason])}>Decline</button>
        </div>
        <DeployResult busy={action.busy} error={action.error} refusal={action.refusal} receipt={action.receipt} />
      </Panel>
      <Panel title={<h2>Evidence</h2>}><Json value={evidence.data ?? []} /></Panel>
      <Panel title={<h2>Raw state</h2>}><Json value={entity} /></Panel>
    </div>
  );
}
