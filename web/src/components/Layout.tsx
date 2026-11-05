import { useQuery } from "@tanstack/react-query";
import { NavLink, Outlet } from "react-router-dom";
import NetworkBanner from "./NetworkBanner";
import Unlock from "./Unlock";
import { shortId } from "../lib/format";
import { useWallet } from "../lib/store";

const TABS = [
  ["/", "Overview"],
  ["/syndicates", "Syndicates"],
  ["/brokers", "Brokers"],
  ["/risks", "Risks"],
  ["/slips", "Slips"],
  ["/policies", "Policies"],
  ["/claims", "Claims"],
  ["/fund", "Fund"],
  ["/admin", "Admin"],
  ["/me", "Me"],
  ["/settings", "Settings"],
] as const;

export default function Layout() {
  const { status, address, lock, client, node, profile, openUnlock } = useWallet();
  const height = useQuery({
    queryKey: ["height", node],
    enabled: !!client,
    refetchInterval: 8_000,
    queryFn: async () => Number(await client!.height()),
  });

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="mark">r</span>
          <div>
            <strong>r-sure</strong>
            <small>insurance placement · subscription · claims</small>
          </div>
        </div>
        <nav className="tabs">
          {TABS.map(([to, label]) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) => (isActive ? "tab active" : "tab")}
            >
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="wallet-chip">
          {status === "unlocked" && address ? (
            <>
              <span className={`dot ${status}`} />
              <span className="mono" title={address}>
                {shortId(address, 6)}
              </span>
              <button className="ghost" onClick={lock}>
                Lock
              </button>
            </>
          ) : (
            <>
              <span className={`dot ${status}`} />
              <button className="ghost" onClick={openUnlock} type="button">
                {status === "error" ? "wallet error" : "Connect wallet"}
              </button>
            </>
          )}
        </div>
      </header>

      <div className="node-line">
        {profile.name} · {node} · height {height.data?.toLocaleString() ?? "…"}
      </div>
      <NetworkBanner />

      <main className="content">
        <Outlet />
      </main>

      <footer className="footer">
        <span>
          r-sure · {profile.name} · no real value · the chain is the backend · source AGPL-3.0-only
        </span>
        <a href="https://github.com/rhovision-org/r-sure" target="_blank" rel="noreferrer">
          Source
        </a>
      </footer>
      <Unlock />
    </div>
  );
}
