import { useState } from "react";
import { useNavigate } from "react-router-dom";
import DeployResult from "../components/DeployResult";
import { Field, Panel } from "../components/ui";
import { createdUri } from "../lib/chain";
import { useWallet } from "../lib/store";
import { useAction } from "../lib/useAction";

const CLASSES = ["engineering", "property", "equipment", "liability", "marine", "cyber"];

export default function BrokerNew() {
  const navigate = useNavigate();
  const client = useWallet((state) => state.client);
  const action = useAction("broker");
  const [name, setName] = useState("");
  const [licence, setLicence] = useState("");
  const [credential, setCredential] = useState("");
  const [commission, setCommission] = useState("1000");
  const [classes, setClasses] = useState<string[]>(["property"]);

  const toggle = (value: string) =>
    setClasses((current) =>
      current.includes(value)
        ? current.filter((item) => item !== value)
        : [...current, value],
    );

  const submit = async () => {
    if (!client) return;
    const profile = {
      name,
      licenceHash: licence,
      credentialUri: credential || undefined,
      commissionBps: Number(commission),
      classes,
    };
    const result = await action.run(
      `register broker ${name}`,
      () =>
        client.write_component_json(
          "broker-book",
          "register",
          JSON.stringify([profile]),
          true,
        ),
      [["read", "broker-book"]],
    );
    const uri = result ? createdUri(result.data) : undefined;
    navigate(uri ? `/brokers/${encodeURIComponent(uri)}` : "/brokers");
  };

  return (
    <div className="stack">
      <Panel title={<h1>Register broker</h1>}>
        <p className="muted">
          The connected wallet becomes the broker owner. The licence hash is an off-chain
          credential anchor, not a claim of regulatory status.
        </p>
        <div className="grid two">
          <Field label="Name"><input value={name} onChange={(e) => setName(e.target.value)} /></Field>
          <Field label="Licence hash"><input value={licence} onChange={(e) => setLicence(e.target.value)} /></Field>
          <Field label="Credential URI" hint="optional"><input value={credential} onChange={(e) => setCredential(e.target.value)} /></Field>
          <Field label="Commission bps" hint="0–3000"><input value={commission} onChange={(e) => setCommission(e.target.value)} inputMode="numeric" /></Field>
        </div>
        <Field label="Classes">
          <div className="row gap wrap">
            {CLASSES.map((value) => (
              <button type="button" key={value} className={`ghost ${classes.includes(value) ? "active" : ""}`} onClick={() => toggle(value)}>
                {value}
              </button>
            ))}
          </div>
        </Field>
        <button className="button" disabled={action.busy || !name || !licence || classes.length === 0} onClick={submit}>
          {action.busy ? "submitting…" : "Register broker"}
        </button>
        <DeployResult busy={action.busy} error={action.error} refusal={action.refusal} receipt={action.receipt} />
      </Panel>
    </div>
  );
}
