import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import DeployResult from "../components/DeployResult";
import EntityHeader from "../components/EntityHeader";
import { Field, Json, Panel } from "../components/ui";
import { slipRole } from "../lib/capabilities";
import { useUriRead } from "../lib/chain";
import { useWallet } from "../lib/store";
import type { SlipState } from "../lib/types";
import { useAction } from "../lib/useAction";

export default function Slip() {
  const { uri } = useParams<{ uri: string }>();
  const decoded = uri ? decodeURIComponent(uri) : "";
  const { client, address } = useWallet();
  const info = useUriRead<SlipState>(decoded, "info");
  const premium = useUriRead(decoded, "premium");
  const subs = useUriRead(decoded, "subscriptions");
  const policy = useUriRead<string | undefined>(decoded, "policy");
  const action = useAction("slip", decoded);
  const [syndicate, setSyndicate] = useState("");
  const [share, setShare] = useState("10000");
  const [fundAmount, setFundAmount] = useState("1000");

  if (!decoded) return <Panel><p className="error">Missing slip URI.</p></Panel>;
  if (info.isLoading) return <Panel><p className="muted">Reading slip…</p></Panel>;
  if (info.error) return <Panel><p className="error">{String(info.error)}</p></Panel>;
  const entity = info.data ?? {};
  const policyUri = typeof policy.data === "string" ? policy.data : undefined;
  const role = slipRole(entity, address);
  const write = (summary: string, arm: string, args: unknown[], ownerFirst = true) =>
    action.run(summary, () => client!.write_uri_json(decoded, arm, JSON.stringify(args), ownerFirst), [["read-uri", decoded]]);

  return (
    <div className="stack">
      <Panel>
        <EntityHeader
          kind="slips"
          uri={decoded}
          title={String(entity.id ?? "Slip")}
          status={String(entity.status ?? "open")}
          actions={<span className="pill">{role.allowed ? role.reason : "read-only"}</span>}
        />
        <div className="grid two">
          <div className="stat"><span className="muted">Premium</span><strong>{String(entity.premiumTotal ?? "—")}</strong></div>
          <div className="stat"><span className="muted">Funded</span><strong>{String(entity.funded ?? 0)}</strong></div>
          <div className="stat"><span className="muted">Accepted</span><strong>{String(entity.insuredAccepted ?? false)}</strong></div>
          <div className="stat"><span className="muted">Expiry height</span><strong>{String(entity.expiryHeight ?? "—")}</strong></div>
        </div>
        {!role.allowed && <p className="muted">{role.reason}.</p>}
      </Panel>

      <Panel
        title={<h2>Insured</h2>}
        actions={<button className="button" disabled={!role.allowed} onClick={() => void write("accept slip", "accept", [])}>Accept</button>}
      >
        <p className="muted">Only the insured can accept. Acceptance is required before bind.</p>
      </Panel>

      <Panel title={<h2>Subscription</h2>}>
        <p className="muted">
          A syndicate manager subscribes a share; the slip calls the syndicate's quote and
          reserves capacity through a one-shot LineGrant.
        </p>
        <div className="grid two">
          <Field label="Syndicate URI"><input value={syndicate} onChange={(e) => setSyndicate(e.target.value)} /></Field>
          <Field label="Share bps"><input value={share} onChange={(e) => setShare(e.target.value)} inputMode="numeric" /></Field>
        </div>
        <button className="button" disabled={!role.allowed || !syndicate} onClick={() => void write("subscribe syndicate", "subscribe", [syndicate, Number(share)])}>
          Subscribe
        </button>
        <Json value={subs.data ?? {}} />
      </Panel>

      <Panel
        title={<h2>Funding and bind</h2>}
        actions={
          <button className="button" disabled={action.busy} onClick={() => void write("bind slip", "bind", [], false)}>
            Bind
          </button>
        }
      >
        <p className="muted">
          Fund the exact premium from the insured's r-cash account. The payment is created
          and deposited into the slip purse in one signed deploy. Bind is permissionless
          once accepted, fully subscribed and funded.
        </p>
        <div className="row gap">
          <input value={fundAmount} onChange={(e) => setFundAmount(e.target.value)} inputMode="numeric" />
          <button
            className="button"
            disabled={!role.allowed || action.busy}
            onClick={() =>
              void action.run(
                "fund slip premium",
                () => client!.slip_fund_premium(decoded, BigInt(fundAmount)),
                [["read-uri", decoded]],
              )
            }
          >
            Fund premium
          </button>
        </div>
        <Json value={premium.data ?? {}} />
        <DeployResult busy={action.busy} error={action.error} refusal={action.refusal} receipt={action.receipt} />
      </Panel>

      <Panel title={<h2>Policy</h2>}>
        {policyUri ? <Link className="button ghost" to={`/policies/${encodeURIComponent(policyUri)}`}>Open policy</Link> : <p className="muted">Not bound yet.</p>}
      </Panel>

      <Panel title={<h2>Raw state</h2>}><Json value={entity} /></Panel>
    </div>
  );
}
