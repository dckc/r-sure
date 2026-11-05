import { useState } from "react";
import { useNavigate } from "react-router-dom";
import DeployResult from "../components/DeployResult";
import { Field, Panel } from "../components/ui";
import { createdUri } from "../lib/chain";
import { useAction } from "../lib/useAction";
import { useWallet } from "../lib/store";

const CLASSES = ["engineering", "property", "equipment", "liability", "marine", "cyber"];

export default function SyndicateNew() {
  const navigate = useNavigate();
  const client = useWallet((state) => state.client);
  const action = useAction("syndicate");
  const [name, setName] = useState("");
  const [asset, setAsset] = useState("REV");
  const [classes, setClasses] = useState<string[]>(["property"]);

  const toggle = (value: string) =>
    setClasses((current) =>
      current.includes(value)
        ? current.filter((item) => item !== value)
        : [...current, value],
    );

  const submit = async () => {
    if (!client) return;
    const profile = { name, assetId: asset, riskAppetite: classes };
    const result = await action.run(
      `create syndicate ${name}`,
      () =>
        client.write_component_json(
          "syndicate-book",
          "create",
          JSON.stringify([profile]),
          true,
        ),
      [["read", "syndicate-book"], ["read", "syndicate-book", "count"]],
    );
    const uri = result ? createdUri(result.data) : undefined;
    navigate(uri ? `/syndicates/${encodeURIComponent(uri)}` : "/syndicates");
  };

  return (
    <div className="stack">
      <Panel title={<h1>Create syndicate</h1>}>
        <p className="muted">
          The connected wallet becomes the syndicate owner and manager. Capital is
          contributed separately; a new syndicate starts at zero capacity.
        </p>
        <div className="grid two">
          <Field label="Name" hint="1–64 characters">
            <input value={name} onChange={(event) => setName(event.target.value)} />
          </Field>
          <Field label="Asset" hint="r-cash asset id">
            <input value={asset} onChange={(event) => setAsset(event.target.value)} />
          </Field>
        </div>
        <Field label="Risk appetite">
          <div className="row gap wrap">
            {CLASSES.map((value) => (
              <button
                type="button"
                key={value}
                className={`ghost ${classes.includes(value) ? "active" : ""}`}
                onClick={() => toggle(value)}
              >
                {value}
              </button>
            ))}
          </div>
        </Field>
        <button className="button" disabled={action.busy || !name || classes.length === 0} onClick={submit}>
          {action.busy ? "submitting…" : "Create syndicate"}
        </button>
        <DeployResult
          busy={action.busy}
          error={action.error}
          refusal={action.refusal}
          receipt={action.receipt}
        />
      </Panel>
    </div>
  );
}
