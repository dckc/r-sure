//! r-sure reference CLI. `doctor`, `manifest`, `classes` and local keystore
//! encryption are live; market commands are added with the SDK write layer.

use std::path::{Path, PathBuf};

use clap::{Parser, Subcommand};
use rcash_chain::address::eth_address_from_public_key;
use rcash_chain::KeyPair;

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
    /// Encrypt a secret into a Web3 v3 keystore document.
    Keystore {
        #[command(subcommand)]
        command: KeystoreCommand,
    },
}

#[derive(Debug, Subcommand)]
enum KeystoreCommand {
    /// Encrypt a 32-byte hex secret. Prints the REV address it belongs to.
    Encrypt {
        /// The secret itself. Prefer --keys/--name so it is not in the process list.
        #[arg(long, conflicts_with_all = ["keys", "name"])]
        secret: Option<String>,
        /// A devnet keys file (`{"name": {"secret": "..."}}`).
        #[arg(long, requires = "name")]
        keys: Option<PathBuf>,
        /// The key name inside --keys.
        #[arg(long, requires = "keys")]
        name: Option<String>,
        #[arg(long)]
        password: String,
        #[arg(long)]
        out: PathBuf,
    },
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
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
        Command::Keystore { command } => {
            let KeystoreCommand::Encrypt {
                secret,
                keys,
                name,
                password,
                out,
            } = command;
            let secret = match (secret, keys, name) {
                (Some(secret), None, None) => secret,
                (None, Some(keys), Some(name)) => secret_from_keys(&keys, &name)?,
                _ => return Err("pass either --secret or --keys with --name".into()),
            };
            println!("{}", encrypt_keystore(&secret, &password, &out)?);
        }
    }
    Ok(())
}

fn secret_from_keys(path: &Path, name: &str) -> Result<String, Box<dyn std::error::Error>> {
    let document: serde_json::Value = serde_json::from_str(&std::fs::read_to_string(path)?)?;
    let secret = document
        .get(name)
        .and_then(|entry| entry.get("secret"))
        .and_then(|value| value.as_str())
        .ok_or_else(|| {
            std::io::Error::other(format!("no secret for {name} in {}", path.display()))
        })?;
    Ok(secret.to_string())
}

fn encrypt_keystore(
    secret: &str,
    password: &str,
    out: &Path,
) -> Result<String, Box<dyn std::error::Error>> {
    let key = KeyPair::from_secret_hex(secret)?;
    let eth = eth_address_from_public_key(key.public_bytes())?;
    let document = rsure_keystore::encrypt(key.secret_bytes(), &eth, password)
        .map_err(std::io::Error::other)?;
    if let Some(parent) = out.parent() {
        std::fs::create_dir_all(parent)?;
    }
    std::fs::write(out, document)?;
    Ok(key.rev_address()?)
}

#[cfg(test)]
mod tests {
    use super::encrypt_keystore;

    #[test]
    fn encrypts_a_generated_key_that_decrypts_back() -> Result<(), Box<dyn std::error::Error>> {
        let key = rcash_chain::KeyPair::generate()?;
        let out = std::env::temp_dir().join(format!("rsure-keystore-{}.json", std::process::id()));
        let address = encrypt_keystore(&key.secret_hex(), "test-password", &out)?;
        assert_eq!(address, key.rev_address()?);
        let document = std::fs::read_to_string(&out)?;
        assert!(document.contains("\"version\":3"));
        assert!(!document.contains("\"secret\""));
        let decrypted =
            rsure_keystore::decrypt(&document, "test-password").map_err(std::io::Error::other)?;
        assert_eq!(decrypted.as_slice(), key.secret_bytes());
        std::fs::remove_file(out)?;
        Ok(())
    }
}
