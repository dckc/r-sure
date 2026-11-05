import { useState } from "react";
import { useNavigate } from "react-router-dom";
import DeployResult from "../components/DeployResult";
import { Field, Panel } from "../components/ui";
import { createdUri } from "../lib/chain";
import { useWallet } from "../lib/store";
import { useAction } from "../lib/useAction";

const CLASSES = ["engineering", "property", "equipment", "liability", "marine", "cyber"];

export default function RiskNew() {
  const navigate = useNavigate();
  const client = useWallet((state) => state.client);
  const action = useAction("risk");
  const [form, setForm] = useState({
    class: "property",
    assetKind: "site",
    assetHash: "",
    declaredValue: "100000",
    requestedLimit: "50000",
    requestedDeductible: "1000",
    periodStart: "0",
    periodEnd: "1000000",
    evidenceKind: "loss-run",
    evidenceHash: "",
    exposureRef: "",
    probabilityBasis: "claims-history",
    consequenceBasis: "declared-value",
    consequenceRef: "",
    broker: "",
  });
  const set = (key: keyof typeof form, value: string) =>
    setForm((current) => ({ ...current, [key]: value }));

  const submit = async () => {
    if (!client) return;
    const req = {
      class: form.class,
      assetRef: { kind: form.assetKind, hash: form.assetHash },
      evidence: [{ kind: form.evidenceKind, hash: form.evidenceHash }],
      triTest: {
        exposureRef: form.exposureRef,
        probabilityBasis: form.probabilityBasis,
        consequenceBasis: form.consequenceBasis,
        consequenceRef: form.consequenceRef,
      },
      periodStart: Number(form.periodStart),
      periodEnd: Number(form.periodEnd),
      declaredValue: Number(form.declaredValue),
      requestedLimit: Number(form.requestedLimit),
      requestedDeductible: Number(form.requestedDeductible),
      broker: form.broker || undefined,
    };
    const result = await action.run(
      `submit ${form.class} risk`,
      () => client.write_component_json("risk-book", "submit", JSON.stringify([req]), true),
      [["read", "risk-book"]],
    );
    const uri = result ? createdUri(result.data) : undefined;
    navigate(uri ? `/risks/${encodeURIComponent(uri)}` : "/risks");
  };

  return (
    <div className="stack">
      <Panel title={<h1>Submit risk</h1>}>
        <p className="muted">
          The connected wallet becomes the insured. The broker must already be registered
          if you name one; the slip factory looks it up by your address.
        </p>
        <div className="grid two">
          <Field label="Class">
            <select value={form.class} onChange={(e) => set("class", e.target.value)}>
              {CLASSES.map((value) => <option key={value}>{value}</option>)}
            </select>
          </Field>
          <Field label="Broker owner id" hint="optional"><input value={form.broker} onChange={(e) => set("broker", e.target.value)} /></Field>
          <Field label="Asset kind"><input value={form.assetKind} onChange={(e) => set("assetKind", e.target.value)} /></Field>
          <Field label="Asset hash"><input value={form.assetHash} onChange={(e) => set("assetHash", e.target.value)} /></Field>
          <Field label="Declared value"><input value={form.declaredValue} onChange={(e) => set("declaredValue", e.target.value)} inputMode="numeric" /></Field>
          <Field label="Requested limit"><input value={form.requestedLimit} onChange={(e) => set("requestedLimit", e.target.value)} inputMode="numeric" /></Field>
          <Field label="Requested deductible"><input value={form.requestedDeductible} onChange={(e) => set("requestedDeductible", e.target.value)} inputMode="numeric" /></Field>
          <Field label="Period start height"><input value={form.periodStart} onChange={(e) => set("periodStart", e.target.value)} inputMode="numeric" /></Field>
          <Field label="Period end height"><input value={form.periodEnd} onChange={(e) => set("periodEnd", e.target.value)} inputMode="numeric" /></Field>
        </div>
        <h3>Evidence</h3>
        <div className="grid two">
          <Field label="Kind"><input value={form.evidenceKind} onChange={(e) => set("evidenceKind", e.target.value)} /></Field>
          <Field label="Hash"><input value={form.evidenceHash} onChange={(e) => set("evidenceHash", e.target.value)} /></Field>
        </div>
        <h3>Tri-test</h3>
        <div className="grid two">
          <Field label="Exposure ref"><input value={form.exposureRef} onChange={(e) => set("exposureRef", e.target.value)} /></Field>
          <Field label="Probability basis"><input value={form.probabilityBasis} onChange={(e) => set("probabilityBasis", e.target.value)} /></Field>
          <Field label="Consequence basis"><input value={form.consequenceBasis} onChange={(e) => set("consequenceBasis", e.target.value)} /></Field>
          <Field label="Consequence ref"><input value={form.consequenceRef} onChange={(e) => set("consequenceRef", e.target.value)} /></Field>
        </div>
        <button className="button" disabled={action.busy || !form.assetHash || !form.evidenceHash || !form.exposureRef || !form.consequenceRef} onClick={submit}>
          {action.busy ? "submitting…" : "Submit risk"}
        </button>
        <DeployResult busy={action.busy} error={action.error} refusal={action.refusal} receipt={action.receipt} />
      </Panel>
    </div>
  );
}
