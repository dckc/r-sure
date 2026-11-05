//! r-sure reference CLI. Scaffold: doctor and manifest commands are live; market commands
//! are added with the SDK write layer.

use clap::{Parser, Subcommand};

#[derive(Debug, Parser)]
#[command(name = "rsure", about = "r-sure insurance primitives client")]
struct Cli {
    #[arg(long, env = "RSURE_NODE", default_value = "http://localhost:40403")]
    node: String,
    #[command(subcommand)]
    command: Command,
}

#[derive(Debug, Subcommand)]
enum Command {
    /// Print the client and contract version boundary.
    Doctor,
    /// Print the component keys this client expects.
    Manifest,
    /// Print the coverage classes.
    Classes,
}

#[tokio::main]
async fn main() {
    let cli = Cli::parse();
    match cli.command {
        Command::Doctor => {
            println!("node: {}", cli.node);
            println!("core: {}", env!("CARGO_PKG_VERSION"));
            println!("term-budget: {} bytes", rsure_core::PROJECT_TERM_BUDGET);
        }
        Command::Manifest => {
            for key in [
                "root",
                "clock",
                "verifier",
                "codec",
                "admin",
                "terms",
                "suremath",
                "rgen",
                "payments",
                "syndicate-book",
                "broker-book",
                "risk-book",
                "slip-factory",
                "line-factory",
                "distribution-factory",
                "fund",
                "policy-factory",
                "claim-factory",
                "policy-book",
                "claim-book",
            ] {
                println!("component:{key}");
            }
        }
        Command::Classes => {
            for class in rsure_core::RiskClass::ALL {
                println!("{}", class.as_str());
            }
        }
    }
}
