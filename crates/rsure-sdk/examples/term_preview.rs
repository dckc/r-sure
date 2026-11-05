//! Write every client-generated Rholang term to a directory.
//!
//! `tools/check_client_terms.sh` runs the node's normalizer over the output. The rendered
//! contract terms already have a normalizer gate; this extends the same gate to the terms
//! the SDK and web client actually send, which is where a free variable escaped once.
//!
//! ```sh
//! cargo run -q -p rsure-sdk --example term_preview -- .devnet/client-terms
//! ```

use std::path::Path;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let directory = std::env::args()
        .nth(1)
        .map(|value| value.into())
        .unwrap_or_else(|| Path::new(".devnet/client-terms").to_path_buf());
    std::fs::create_dir_all(&directory)?;

    let payments = "rho:id:payments";
    let mut terms = vec![
        ("fund-1", rsure_sdk::funding::fund_term(payments, 1)),
        ("fund-1000", rsure_sdk::funding::fund_term(payments, 1_000)),
        (
            "fund-20000",
            rsure_sdk::funding::fund_term(payments, 20_000),
        ),
        (
            "premium",
            rsure_sdk::funding::payment_term(
                payments,
                "rho:id:slip",
                "fundPremium",
                "*deployerId, ",
                "",
                1_000,
            ),
        ),
        (
            "syndicate-contribute",
            rsure_sdk::funding::payment_term(
                payments,
                "rho:id:syndicate",
                "contribute",
                "*deployerId, ",
                "",
                6_000,
            ),
        ),
        (
            "fund-contribute",
            rsure_sdk::funding::payment_term(
                payments,
                "rho:id:fund",
                "contribute",
                "",
                r#", "pol:slip:1""#,
                100,
            ),
        ),
        (
            "read-sample",
            rsure_sdk::wire::call_term("rho:id:component", "info", &[])?,
        ),
        (
            "write-sample",
            rsure_sdk::wire::call_term_signed(
                "rho:id:component",
                "info",
                &["*deployerId".to_string()],
            )?,
        ),
        (
            "resolve-sample",
            rsure_sdk::wire::resolve_term("rho:id:root", "component:clock", 1)?,
        ),
    ];

    for (name, term) in terms.drain(..) {
        std::fs::write(directory.join(format!("{name}.rho")), term)?;
    }
    println!(
        "term_preview: {} terms in {}",
        std::fs::read_dir(&directory)?.count(),
        directory.display()
    );
    Ok(())
}
