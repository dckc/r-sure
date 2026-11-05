import { useEffect, useState } from "react";
import { DEVNET, manifestUrl } from "../lib/network";
import { useWallet } from "../lib/store";
import { ErrorBox, Field, Panel, StatusPill } from "../components/ui";

export default function Settings() {
  const {
    node,
    profile,
    manifest,
    readiness,
    address,
    status,
    profiles,
    setNode,
    setManifest,
    refreshReadiness,
    exportKeystore,
    lock,
  } = useWallet();
  const [nodeInput, setNodeInput] = useState(node);
  const [manifestInput, setManifestInput] = useState(manifest ?? "");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [faucetMessage, setFaucetMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => setNodeInput(node), [node]);
  useEffect(() => setManifestInput(manifest ?? ""), [manifest]);

  const applyManifest = async () => {
    setBusy(true);
    setError(null);
    try {
      await setManifest(manifestInput);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  };

  const faucet = async () => {
    if (!address) return;
    setBusy(true);
    setFaucetMessage(null);
    setError(null);
    try {
      const client = useWallet.getState().clientOrThrow();
      const envelope = JSON.parse(await client.faucet(address)) as { ok?: boolean; message?: string };
      if (!envelope.ok) throw new Error(envelope.message ?? "faucet refused");
      setFaucetMessage("Faucet drip submitted.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  };

  const exportWallet = async () => {
    setBusy(true);
    setError(null);
    try {
      const document = await exportKeystore(password);
      const blob = new Blob([document], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const anchor = window.document.createElement("a");
      anchor.href = url;
      anchor.download = "rsure-keystore.json";
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="stack">
      <Panel title={<h1>Settings</h1>}>
        <p className="muted small">
          The app has no server. The node and the install manifest are the whole
          configuration; component URIs are resolved from the Root.
        </p>
        <div className="grid two">
          <dl className="kv">
            <dt>profile</dt><dd>{profile.name}</dd>
            <dt>node</dt><dd className="mono small">{node}</dd>
            <dt>manifest URL</dt><dd className="mono small">{manifestUrl(profile)}</dd>
            <dt>network id</dt><dd>{readiness.networkId ?? "—"}</dd>
            <dt>shard</dt><dd>{readiness.shard ?? "—"}</dd>
            <dt>readiness</dt><dd><StatusPill status={readiness.state} /></dd>
          </dl>
          <div>
            <div className="row gap wrap">
              <button className="ghost" onClick={() => void setNode(DEVNET.node)}>Use local devnet</button>
              <button className="ghost" onClick={() => void refreshReadiness()}>Recheck</button>
            </div>
            <Field label="Node URL"><input value={nodeInput} onChange={(e) => setNodeInput(e.target.value)} className="mono" /></Field>
            <button disabled={busy || nodeInput === node} onClick={() => void setNode(nodeInput)}>Connect node</button>
          </div>
        </div>
        {readiness.error && <p className="error">{readiness.error}</p>}
      </Panel>

      <Panel title={<h2>Manifest</h2>}>
        <p className="muted small">
          Paste <code>deployments/devnet.json</code> when the sync script has not run. The
          Root URI is the authority; component URIs are resolved from it.
        </p>
        <Field label="Manifest JSON">
          <textarea rows={10} value={manifestInput} onChange={(e) => setManifestInput(e.target.value)} className="mono" />
        </Field>
        <button className="button" onClick={applyManifest} disabled={busy || !manifestInput}>Apply manifest</button>
      </Panel>

      <Panel title={<h2>Wallet and funding</h2>}>
        {status !== "unlocked" ? (
          <p className="muted">Unlock a wallet to use the faucet and export a keystore.</p>
        ) : (
          <>
            <dl className="kv">
              <dt>address</dt><dd className="mono small">{address}</dd>
              <dt>saved profiles</dt><dd>{profiles.length}</dd>
            </dl>
            <div className="row gap wrap">
              <button className="ghost" onClick={faucet} disabled={busy}>Request faucet drip</button>
              <button className="ghost" onClick={lock}>Lock wallet</button>
            </div>
            {faucetMessage && <p className="muted small">{faucetMessage}</p>}
            <Field label="Keystore password" hint="to export the encrypted file">
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            </Field>
            <button onClick={exportWallet} disabled={busy || password.length < 8}>Export keystore</button>
          </>
        )}
        <ErrorBox error={error} />
      </Panel>

      <Panel title={<h2>Resolved components</h2>}>
        {!readiness.components || Object.keys(readiness.components).length === 0 ? (
          <p className="muted">Resolve the Root to see the installed components.</p>
        ) : (
          <div className="list">
            {Object.entries(readiness.components).map(([key, component]) => (
              <div className="list-row" key={key}>
                <span className="mono small">{key}</span>
                <span className="mono small">{component.uri}</span>
                <span className="pill">v{component.version}</span>
              </div>
            ))}
          </div>
        )}
      </Panel>
    </div>
  );
}
