import { useParams } from "react-router-dom";
import DeployResult from "../components/DeployResult";
import EntityHeader from "../components/EntityHeader";
import { Json, Panel } from "../components/ui";
import { isOwner } from "../lib/capabilities";
import { useUriRead } from "../lib/chain";
import { useWallet } from "../lib/store";
import type { BrokerState } from "../lib/types";
import { useAction } from "../lib/useAction";

export default function Broker() {
  const { uri } = useParams<{ uri: string }>();
  const decoded = uri ? decodeURIComponent(uri) : "";
  const { client, address } = useWallet();
  const info = useUriRead<BrokerState>(decoded, "info");
  const profile = useUriRead(decoded, "profile");
  const slips = useUriRead(decoded, "slips");
  const action = useAction("broker", decoded);

  if (!decoded) return <Panel><p className="error">Missing broker URI.</p></Panel>;
  if (info.isLoading) return <Panel><p className="muted">Reading broker…</p></Panel>;
  if (info.error) return <Panel><p className="error">{String(info.error)}</p></Panel>;
  const entity = info.data ?? {};
  const owner = isOwner(entity, address);
  const write = (summary: string, arm: string, args: unknown[]) =>
    action.run(summary, () => client!.write_uri_json(decoded, arm, JSON.stringify(args), true), [["read-uri", decoded]]);

  return (
    <div className="stack">
      <Panel>
        <EntityHeader
          kind="brokers"
          uri={decoded}
          title={String(entity.name ?? "Broker")}
          status={String(entity.status ?? "active")}
          actions={<span className="pill">{owner.allowed ? "owner" : "read-only"}</span>}
        />
        <div className="grid two">
          <div className="stat"><span className="muted">Owner</span><strong className="mono small">{String(entity.ownerId ?? "—")}</strong></div>
          <div className="stat"><span className="muted">Commission</span><strong>{String(entity.commissionBps ?? "—")} bps</strong></div>
        </div>
        {!owner.allowed && <p className="muted">{owner.reason}.</p>}
      </Panel>
      <Panel
        title={<h2>Lifecycle</h2>}
        actions={
          <>
            <button className="button ghost" disabled={!owner.allowed} onClick={() => void write("pause broker", "pause", [])}>Pause</button>
            <button className="button ghost" disabled={!owner.allowed} onClick={() => void write("resume broker", "resume", [])}>Resume</button>
          </>
        }
      >
        <p className="muted">A paused broker cannot open new slips; existing policies are unaffected.</p>
        <DeployResult busy={action.busy} error={action.error} refusal={action.refusal} receipt={action.receipt} />
      </Panel>
      <Panel title={<h2>Profile</h2>}><Json value={profile.data ?? {}} /></Panel>
      <Panel title={<h2>Slips</h2>}><Json value={slips.data ?? {}} /></Panel>
    </div>
  );
}
