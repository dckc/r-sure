import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import DeployResult from "../components/DeployResult";
import { Json, Panel } from "../components/ui";
import { useRead } from "../lib/chain";
import { useWallet } from "../lib/store";
import { useAction } from "../lib/useAction";

export default function Fund() {
  const { client } = useWallet();
  const info = useRead("fund", "info");
  const balance = useRead<number>("fund", "balance");
  const shortfalls = useRead("fund", "shortfalls");
  const action = useAction("fund");
  const [amount, setAmount] = useState("100");
  const [policyId, setPolicyId] = useState("");
  const fundUri = useQuery({
    queryKey: ["resolve", "fund"],
    enabled: Boolean(client),
    queryFn: async () => {
      const resolved = JSON.parse(await client!.resolve("fund")) as { ok?: boolean; uri?: string; message?: string };
      if (!resolved.ok || !resolved.uri) throw new Error(resolved.message ?? "fund unresolved");
      return resolved.uri;
    },
  });

  return (
    <div className="stack">
      <Panel title={<h1>Central fund</h1>}>
        <p className="muted">
          The fund receives the central-fund levy and covers the part of a payable that the
          lines cannot pay. Cover is a 2-of-3 admin action.
        </p>
        <div className="grid two">
          <div className="stat"><span className="muted">Asset</span><strong>{String((info.data as Record<string, unknown> | undefined)?.assetId ?? "—")}</strong></div>
          <div className="stat"><span className="muted">Balance</span><strong>{balance.data ?? "…"}</strong></div>
        </div>
      </Panel>
      <Panel title={<h2>Contribute</h2>}>
        <p className="muted">A contribution is a payment attached to a policy id.</p>
        <div className="row gap">
          <input value={amount} onChange={(e) => setAmount(e.target.value)} inputMode="numeric" />
          <input value={policyId} onChange={(e) => setPolicyId(e.target.value)} placeholder="policy id" />
          <button
            className="button"
            disabled={action.busy || !fundUri.data || !policyId}
            onClick={() =>
              void action.run(
                "contribute to fund",
                () => client!.fund_contribute(fundUri.data!, BigInt(amount), policyId),
                [["read", "fund"]],
              )
            }
          >
            Contribute
          </button>
        </div>
        {fundUri.error && <p className="error">{String(fundUri.error)}</p>}
        <DeployResult busy={action.busy} error={action.error} refusal={action.refusal} receipt={action.receipt} />
      </Panel>
      <Panel title={<h2>Parameters</h2>}><Json value={info.data ?? {}} /></Panel>
      <Panel title={<h2>Shortfalls</h2>}><Json value={shortfalls.data ?? {}} /></Panel>
      <Panel title={<h2>Admin</h2>}>
        <p className="muted">
          Fund cover and parameter changes use the fund admin set and a 2-of-3 signature
          flow. Open the Admin page to build and sign the payload.
        </p>
      </Panel>
    </div>
  );
}
