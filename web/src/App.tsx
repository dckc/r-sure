const ROUTES = [
  ["Explore", "Curated market catalogue"],
  ["Syndicate", "Capacity, quotes and lines"],
  ["Broker", "Registered intermediary"],
  ["Risk", "Submit an engineering risk"],
  ["Slip", "Place, subscribe and bind"],
  ["Policy", "Lines, premium and aggregate"],
  ["Claim", "Notify, assess, agree, settle"],
  ["Fund", "Central fund balance and covers"],
  ["Admin", "2-of-3 pause and thresholds"],
  ["Me", "Owned risks, slips, policies and claims"],
];

export function App() {
  return (
    <main className="shell">
      <header>
        <h1>r-sure</h1>
        <p className="warn">
          Devnet-only, unaudited, no real value. Not an insurer and not affiliated with
          Lloyd&apos;s.
        </p>
      </header>
      <nav className="grid">
        {ROUTES.map(([name, description]) => (
          <section key={name} className="card">
            <h2>{name}</h2>
            <p>{description}</p>
            <span className="pill">scaffold</span>
          </section>
        ))}
      </nav>
      <footer>
        <p>
          Disabled placeholders: search, fiat ramps, KYC, evidence upload, notifications,
          reinsurance, endorsements and renewals. There is no indexer; discovery is a curated
          catalogue plus share links.
        </p>
      </footer>
    </main>
  );
}
