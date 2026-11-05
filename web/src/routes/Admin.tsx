import { useState } from "react";
import DeployResult from "../components/DeployResult";
import { Field, Json, Panel, StatusPill } from "../components/ui";
import { parseRead } from "../lib/api";
import { useRead } from "../lib/chain";
import { useWallet } from "../lib/store";
import { useAction } from "../lib/useAction";
import { Rsure } from "../wasm";

const ACTIONS = ["pauseAll", "resumeAll"];

export default function Admin() {
  const { client, node, manifest, profiles, address } = useWallet();
  const keys = useRead("admin", "keys");
  const paused = useRead<boolean>("admin", "isPaused");
  const nonce = useRead<number>("admin", "nonce");
  const action = useAction("admin");
  const [selectedAction, setSelectedAction] = useState("pauseAll");
  const [signatures, setSignatures] = useState<string[]>([]);
  const [payload, setPayload] = useState<string | null>(null);
  const [passwords, setPasswords] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  const build = async (): Promise<{ payload: string; signatures: string[] } | null> => {
    if (!client || !node || !manifest) return null;
    setError(null);
    if (nonce.data === undefined) {
      setError("Reading the admin nonce; try again in a moment.");
      return null;
    }
    const next = nonce.data + 1;
    try {
      const read = parseRead<string>(
        await client.read_component_json(
          "codec",
          "adminPayload",
          JSON.stringify(["admin", next, selectedAction, []]),
        ),
      );
      const text = String(read.data);
      const collected: string[] = [];
      for (const profile of profiles) {
        const password = passwords[profile.address];
        if (!password) continue;
        const signer = new Rsure(node, manifest);
        signer.unlock(profile.document, password);
        collected.push(signer.sign_payload(text));
        signer.lock();
      }
      if (collected.length === 0) {
        setError("Enter the password for at least two saved admin profiles.");
        return null;
      }
      setPayload(text);
      setSignatures(collected);
      return { payload: text, signatures: collected };
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : String(cause));
      return null;
    }
  };

  const sign = async () => {
    const built = await build();
    if (!built) return;
  };

  const submit = async () => {
    if (!client) return;
    // Always rebuild: the payload binds the nonce and action, and both change between
    // submissions. Reusing a signed payload from a previous action would verify against
    // the wrong digest.
    const built = await build();
    if (!built) return;
    const next = (nonce.data ?? 0) + 1;
    const sigLiteral = `[${built.signatures
      .map((signature) => `"${signature}".hexToBytes()`)
      .join(", ")}]`;
    await action.run(
      `${selectedAction} at nonce ${next}`,
      () =>
        client.write_component_json(
          "admin",
          "admin",
          JSON.stringify([next, selectedAction, [], { raw: sigLiteral }]),
          false,
        ),
      [["read", "admin"], ["read", "admin", "isPaused"], ["read", "admin", "nonce"]],
    );
  };

  return (
    <div className="stack">
      <Panel title={<h1>Admin</h1>}>
        <div className="row gap wrap">
          <StatusPill status={paused.data ? "paused" : "active"} />
          <span className="pill">nonce {nonce.data ?? "…"}</span>
          <span className="pill">threshold 2 of 3</span>
        </div>
        <p className="muted">
          Pause blocks new risk and capacity creation; claims, settlement, expiry and
          refunds stay available. Signatures are collected from saved profiles; the payload
          is produced by the deployed Codec, never rebuilt in the browser.
        </p>
      </Panel>

      <Panel title={<h2>Pause switch</h2>}>
        <div className="grid two">
          <Field label="Action">
            <select value={selectedAction} onChange={(e) => setSelectedAction(e.target.value)}>
              {ACTIONS.map((value) => <option key={value}>{value}</option>)}
            </select>
          </Field>
          <Field label="Next nonce"><span className="mono">{Number(nonce.data ?? 0) + 1}</span></Field>
        </div>
        {profiles.length === 0 && <p className="muted">No saved profiles. Create or import admin wallets in Settings.</p>}
        {profiles.map((profile) => (
          <div className="row gap" key={profile.address}>
            <span className="mono small">{profile.label || profile.address}</span>
            <input
              type="password"
              placeholder="password"
              value={passwords[profile.address] ?? ""}
              onChange={(event) => setPasswords((current) => ({ ...current, [profile.address]: event.target.value }))}
            />
          </div>
        ))}
        <div className="row gap">
          <button className="button ghost" disabled={nonce.data === undefined || action.busy} onClick={sign}>
            Build and sign
          </button>
          <button className="button" disabled={nonce.data === undefined || action.busy} onClick={submit}>
            Submit 2-of-3
          </button>
        </div>
        {error && <p className="error">{error}</p>}
        <DeployResult busy={action.busy} error={action.error} refusal={action.refusal} receipt={action.receipt} />
      </Panel>

      <Panel title={<h2>Current admin set</h2>}><Json value={keys.data ?? []} /></Panel>
      <Panel title={<h2>Signed payload</h2>}>
        {payload ? <Json value={{ payload, signatures }} /> : <p className="muted">Not built yet.</p>}
      </Panel>
      <Panel title={<h2>Wallet</h2>}><p className="mono small">{address ?? "locked"}</p></Panel>
    </div>
  );
}
