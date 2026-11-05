import { useEffect } from "react";
import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Admin from "./routes/Admin";
import Broker from "./routes/Broker";
import BrokerNew from "./routes/BrokerNew";
import Brokers from "./routes/Brokers";
import Claim from "./routes/Claim";
import Claims from "./routes/Claims";
import Disabled from "./routes/Disabled";
import Fund from "./routes/Fund";
import Me from "./routes/Me";
import Overview from "./routes/Overview";
import Policies from "./routes/Policies";
import Policy from "./routes/Policy";
import Risk from "./routes/Risk";
import RiskNew from "./routes/RiskNew";
import Risks from "./routes/Risks";
import Settings from "./routes/Settings";
import Slip from "./routes/Slip";
import SlipNew from "./routes/SlipNew";
import Slips from "./routes/Slips";
import Syndicate from "./routes/Syndicate";
import SyndicateNew from "./routes/SyndicateNew";
import Syndicates from "./routes/Syndicates";
import { useWallet } from "./lib/store";

export default function App() {
  const boot = useWallet((state) => state.boot);
  useEffect(() => {
    void boot();
  }, [boot]);

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Overview />} />
        <Route path="syndicates" element={<Syndicates />} />
        <Route path="syndicates/new" element={<SyndicateNew />} />
        <Route path="syndicates/:uri" element={<Syndicate />} />
        <Route path="brokers" element={<Brokers />} />
        <Route path="brokers/new" element={<BrokerNew />} />
        <Route path="brokers/:uri" element={<Broker />} />
        <Route path="risks" element={<Risks />} />
        <Route path="risks/new" element={<RiskNew />} />
        <Route path="risks/:uri" element={<Risk />} />
        <Route path="slips" element={<Slips />} />
        <Route path="slips/new" element={<SlipNew />} />
        <Route path="slips/:uri" element={<Slip />} />
        <Route path="policies" element={<Policies />} />
        <Route path="policies/:uri" element={<Policy />} />
        <Route path="claims" element={<Claims />} />
        <Route path="claims/:uri" element={<Claim />} />
        <Route path="fund" element={<Fund />} />
        <Route path="admin" element={<Admin />} />
        <Route path="me" element={<Me />} />
        <Route path="settings" element={<Settings />} />
        <Route path="search" element={<Disabled title="Global search" reason="There is no indexer. Browse the on-chain books or paste a rho:id URI." />} />
        <Route path="ramps" element={<Disabled title="Fiat ramps" reason="A ramp is a licensed off-chain partner, not an on-chain contract." />} />
        <Route path="kyc" element={<Disabled title="Identity checks" reason="Identity is off-chain; the chain sees a deployer key, not a person." />} />
        <Route path="notifications" element={<Disabled title="Notifications" reason="This client has no event stream; poll the pages or run your own indexer." />} />
        <Route path="uploads" element={<Disabled title="Evidence uploads" reason="Only evidence hashes are anchored on-chain. Store the file elsewhere." />} />
        <Route path="*" element={<Disabled title="Not found" reason="That route does not exist." />} />
      </Route>
    </Routes>
  );
}
