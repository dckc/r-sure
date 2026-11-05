import { useState } from "react";
import { Link } from "react-router-dom";
import { Field, Json, Panel } from "../components/ui";
import { useRead } from "../lib/chain";
import { useWallet } from "../lib/store";

export default function Me() {
  const { client, address, status } = useWallet();
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [amount, setAmount] = useState("1000");
  const risks = useRead("risk-book", "byInsured", [address ?? ""], { enabled: Boolean(address) });
  const policies = useRead("policy-book", "byInsured", [address ?? ""], { enabled: Boolean(address) });
  const claims = useRead("claim-book", "byInsured", [address ?? ""], { enabled: Boolean(address) });
  const syndicate = useRead("syndicate-book", "syndicateOf", [address ?? ""], { enabled: Boolean(address) });
  const broker = useRead("broker-book", "brokerOf", [address ?? ""], { enabled: Boolean(address) });

  if (!client || !address || status !== "unlocked") {
    return <Panel><p className="muted">Unlock a wallet to see owned risks, policies and claims.</p></Panel>;
  }

  const faucet = async () => {
    setError(null);
    setMessage(null);
    try {
      const result = JSON.parse(await client.faucet(address)) as { ok?: boolean; message?: string };
      if (!result.ok) throw new Error(result.message ?? "faucet refused");
      setMessage("Faucet drip submitted. Re-read the balance on the Payments page.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    }
  };

  return (
    <div className="stack">
      <Panel title={<h1>My position</h1>}>
        <Field label="Address"><span className="mono small">{address}</span></Field>
        <div className="row gap">
          <button className="button ghost" onClick={faucet}>Request devnet REV</button>
          <input value={amount} onChange={(e) => setAmount(e.target.value)} inputMode="numeric" />
          <button
            className="button"
            onClick={async () => {
              setError(null);
              try {
                const result = JSON.parse(await client.fund_account_rev(BigInt(amount))) as { ok?: boolean; message?: string };
                if (!result.ok) throw new Error(result.message ?? "funding refused");
                setMessage("Funded the r-cash account from the native REV vault.");
              } catch (cause) {
                setError(cause instanceof Error ? cause.message : String(cause));
              }
            }}
          >
            Fund r-cash account
          </button>
          <Link className="button ghost" to="/settings">Wallet settings</Link>
        </div>
        {message && <p className="muted">{message}</p>}
        {error && <p className="error">{error}</p>}
      </Panel>

      <Panel title={<h2>Syndicate</h2>}>
        <Json value={syndicate.data ?? {}} />
      </Panel>
      <Panel title={<h2>Broker</h2>}>
        <Json value={broker.data ?? {}} />
      </Panel>
      <Panel title={<h2>Risks</h2>}><Json value={risks.data ?? {}} /></Panel>
      <Panel title={<h2>Policies</h2>}><Json value={policies.data ?? {}} /></Panel>
      <Panel title={<h2>Claims</h2>}><Json value={claims.data ?? {}} /></Panel>
    </div>
  );
}
