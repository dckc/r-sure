import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import DeployResult from "../components/DeployResult";
import { Field, Panel } from "../components/ui";
import { useWallet } from "../lib/store";
import { useAction } from "../lib/useAction";

const CLASSES = ["engineering", "property", "equipment", "liability", "marine", "cyber"];

export default function SlipNew() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const { client, address } = useWallet();
  const action = useAction("slip");
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState({
    riskId: params.get("riskId") ?? "",
    riskUri: params.get("riskUri") ?? "",
    coverageClass: params.get("class") ?? "property",
    assetId: "REV",
    aggregateLimit: "5000",
    perClaimLimit: "1000",
    deductible: "0",
    premiumTotal: "1000",
    periodStartHeight: params.get("start") ?? "0",
    periodEndHeight: params.get("end") ?? "1000000",
    waitingBlocks: "0",
    noticeBlocks: "1000",
    runOffBlocks: "100",
    standardClaimMax: "1000",
    minSyndicates: "1",
    maxSyndicates: "1",
    brokerCommissionBps: "1000",
    centralFundBps: "250",
    evidencePolicy: "optional",
    claimsLeadPolicy: "lead",
    expiryHeight: params.get("end") ?? "1000000",
  });
  const set = (key: keyof typeof form, value: string) =>
    setForm((current) => ({ ...current, [key]: value }));

  const submit = async () => {
    if (!client || !address) return;
    const terms = {
      coverageClass: form.coverageClass,
      assetId: form.assetId,
      aggregateLimit: Number(form.aggregateLimit),
      perClaimLimit: Number(form.perClaimLimit),
      deductible: Number(form.deductible),
      premiumTotal: Number(form.premiumTotal),
      periodStartHeight: Number(form.periodStartHeight),
      periodEndHeight: Number(form.periodEndHeight),
      waitingBlocks: Number(form.waitingBlocks),
      noticeBlocks: Number(form.noticeBlocks),
      runOffBlocks: Number(form.runOffBlocks),
      standardClaimMax: Number(form.standardClaimMax),
      minSyndicates: Number(form.minSyndicates),
      maxSyndicates: Number(form.maxSyndicates),
      brokerCommissionBps: Number(form.brokerCommissionBps),
      centralFundBps: Number(form.centralFundBps),
      evidencePolicy: form.evidencePolicy,
      claimsLeadPolicy: form.claimsLeadPolicy,
    };
    if (terms.perClaimLimit > terms.aggregateLimit) {
      setError("Per-claim limit cannot exceed the aggregate limit.");
      return;
    }
    if (terms.deductible >= terms.perClaimLimit) {
      setError("Deductible must be below the per-claim limit.");
      return;
    }
    if (terms.brokerCommissionBps + terms.centralFundBps > 3000) {
      setError("Commission plus fund bps must not exceed 3000.");
      return;
    }
    setError(null);
    const req = {
      riskId: form.riskId,
      riskUri: form.riskUri,
      insured: address,
      class: form.coverageClass,
      terms,
      expiryHeight: Number(form.expiryHeight),
    };
    const result = await action.run(
      `open slip for ${form.riskId}`,
      () => client.write_component_json("slip-factory", "open", JSON.stringify([req]), true),
      [["catalogue"]],
    );
    if (result) {
      const envelope = result as { data?: unknown };
      const data = envelope.data as unknown;
      const uri = Array.isArray(data) ? data[data.length - 1] : undefined;
      if (typeof uri === "string") navigate(`/slips/${encodeURIComponent(uri)}`);
      else navigate("/slips");
    }
  };

  return (
    <div className="stack">
      <Panel title={<h1>Open slip</h1>}>
        <p className="muted">
          The broker opens the slip for the insured. Terms are validated and hashed by
          CoverTerms; the slip is not a policy until every share subscribes, the insured
          accepts, the premium is funded and bind runs.
        </p>
        <div className="grid two">
          <Field label="Risk id"><input value={form.riskId} onChange={(e) => set("riskId", e.target.value)} /></Field>
          <Field label="Risk URI"><input value={form.riskUri} onChange={(e) => set("riskUri", e.target.value)} /></Field>
          <Field label="Cover class">
            <select value={form.coverageClass} onChange={(e) => set("coverageClass", e.target.value)}>
              {CLASSES.map((value) => <option key={value}>{value}</option>)}
            </select>
          </Field>
          <Field label="Asset"><input value={form.assetId} onChange={(e) => set("assetId", e.target.value)} /></Field>
          <Field label="Aggregate limit"><input value={form.aggregateLimit} onChange={(e) => set("aggregateLimit", e.target.value)} inputMode="numeric" /></Field>
          <Field label="Per-claim limit"><input value={form.perClaimLimit} onChange={(e) => set("perClaimLimit", e.target.value)} inputMode="numeric" /></Field>
          <Field label="Deductible"><input value={form.deductible} onChange={(e) => set("deductible", e.target.value)} inputMode="numeric" /></Field>
          <Field label="Premium total"><input value={form.premiumTotal} onChange={(e) => set("premiumTotal", e.target.value)} inputMode="numeric" /></Field>
          <Field label="Period start"><input value={form.periodStartHeight} onChange={(e) => set("periodStartHeight", e.target.value)} inputMode="numeric" /></Field>
          <Field label="Period end"><input value={form.periodEndHeight} onChange={(e) => set("periodEndHeight", e.target.value)} inputMode="numeric" /></Field>
          <Field label="Broker commission bps"><input value={form.brokerCommissionBps} onChange={(e) => set("brokerCommissionBps", e.target.value)} inputMode="numeric" /></Field>
          <Field label="Central fund bps"><input value={form.centralFundBps} onChange={(e) => set("centralFundBps", e.target.value)} inputMode="numeric" /></Field>
          <Field label="Expiry height"><input value={form.expiryHeight} onChange={(e) => set("expiryHeight", e.target.value)} inputMode="numeric" /></Field>
        </div>
        {error && <p className="error">{error}</p>}
        <button className="button" disabled={action.busy || !form.riskId || !form.riskUri} onClick={submit}>
          {action.busy ? "opening…" : "Open slip"}
        </button>
        <DeployResult busy={action.busy} error={action.error} refusal={action.refusal} receipt={action.receipt} />
      </Panel>
    </div>
  );
}
