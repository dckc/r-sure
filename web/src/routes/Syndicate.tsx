import { useState } from "react";
import { useParams } from "react-router-dom";
import DeployResult from "../components/DeployResult";
import EntityHeader from "../components/EntityHeader";
import { Field, Json, Panel, StatusPill } from "../components/ui";
import { syndicateRole } from "../lib/capabilities";
import { useUriRead } from "../lib/chain";
import { useWallet } from "../lib/store";
import type { SyndicateState } from "../lib/types";
import { useAction } from "../lib/useAction";

export default function Syndicate() {
  const { uri } = useParams<{ uri: string }>();
  const decoded = uri ? decodeURIComponent(uri) : "";
  const { client, address } = useWallet();
  const info = useUriRead<SyndicateState>(decoded, "info");
  const capacity = useUriRead(decoded, "capacity");
  const members = useUriRead(decoded, "members");
  const quotes = useUriRead(decoded, "quotes");
  const lines = useUriRead(decoded, "lines");
  const action = useAction("syndicate", decoded);
  const [manager, setManager] = useState("");
  const [amount, setAmount] = useState("0");
  const [contribute, setContribute] = useState("1000");

  if (!decoded) return <Panel><p className="error">Missing syndicate URI.</p></Panel>;
  if (info.isLoading) return <Panel><p className="muted">Reading syndicate…</p></Panel>;
  if (info.error) return <Panel><p className="error">{String(info.error)}</p></Panel>;

  const entity = info.data ?? {};
  const role = syndicateRole(entity, address);
  const cap = (capacity.data ?? {}) as Record<string, number>;

  const write = (summary: string, arm: string, args: unknown[]) =>
    action.run(
      summary,
      () =>
        client!.write_uri_json(decoded, arm, JSON.stringify(args), true),
      [["read-uri", decoded]],
    );

  return (
    <div className="stack">
      <Panel>
        <EntityHeader
          kind="syndicates"
          uri={decoded}
          title={String(entity.name ?? "Syndicate")}
          status={String(entity.status ?? "active")}
          meta={info.data ? undefined : undefined}
          actions={<StatusPill status={role.allowed ? role.reason : "read-only"} />}
        />
        <div className="grid two">
          <div className="stat"><span className="muted">Capital</span><strong>{cap.capital ?? "…"}</strong></div>
          <div className="stat"><span className="muted">Free</span><strong>{cap.free ?? "…"}</strong></div>
          <div className="stat"><span className="muted">Committed</span><strong>{cap.committed ?? "…"}</strong></div>
          <div className="stat"><span className="muted">Written</span><strong>{cap.written ?? "…"}</strong></div>
        </div>
        {!role.allowed && <p className="muted">{role.reason}.</p>}
      </Panel>

      <Panel title={<h2>Owner and manager</h2>}>
        <div className="grid two">
          <Field label="Owner"><span className="mono small">{String(entity.ownerId ?? "—")}</span></Field>
          <Field label="Manager"><span className="mono small">{String(entity.managerId ?? "—")}</span></Field>
        </div>
        <div className="row gap">
          <input value={manager} onChange={(event) => setManager(event.target.value)} placeholder="new manager id" />
          <button className="button" disabled={!role.allowed || !manager} onClick={() => void write("set manager", "setManager", [manager])}>
            Set manager
          </button>
        </div>
      </Panel>

      <Panel title={<h2>Capital</h2>}>
        <p className="muted">
          Contribution creates a payment from the connected wallet's r-cash account and
          deposits it into the syndicate purse in one signed deploy. Withdrawal is owner-only
          and bounded by free capacity.
        </p>
        <div className="row gap">
          <input value={contribute} onChange={(event) => setContribute(event.target.value)} inputMode="numeric" />
          <button
            className="button"
            disabled={!address || action.busy}
            onClick={() =>
              void action.run(
                "contribute capital",
                () => client!.syndicate_contribute(decoded, BigInt(contribute)),
                [["read-uri", decoded]],
              )
            }
          >
            Contribute
          </button>
        </div>
        <div className="row gap">
          <input value={amount} onChange={(event) => setAmount(event.target.value)} inputMode="numeric" />
          <button className="button" disabled={!role.allowed || amount === "0"} onClick={() => void write("withdraw capital", "withdrawCapital", [Number(amount)])}>
            Withdraw
          </button>
        </div>
      </Panel>

      <Panel
        title={<h2>Lifecycle</h2>}
        actions={
          <>
            <button className="button ghost" disabled={!role.allowed} onClick={() => void write("suspend syndicate", "suspend", [])}>Suspend</button>
            <button className="button ghost" disabled={!role.allowed} onClick={() => void write("resume syndicate", "resume", [])}>Resume</button>
          </>
        }
      >
        <p className="muted">Suspension blocks new quotes and lines; existing lines remain payable.</p>
        <DeployResult busy={action.busy} error={action.error} refusal={action.refusal} receipt={action.receipt} />
      </Panel>

      <Panel title={<h2>Members</h2>}>
        <pre className="json">{JSON.stringify(members.data ?? {}, null, 2)}</pre>
      </Panel>
      <Panel title={<h2>Quotes and lines</h2>}>
        <div className="grid two">
          <div><h3>Quotes</h3><Json value={quotes.data ?? {}} /></div>
          <div><h3>Lines</h3><Json value={lines.data ?? {}} /></div>
        </div>
      </Panel>
      <Panel title={<h2>Raw state</h2>}><Json value={entity} /></Panel>
    </div>
  );
}
