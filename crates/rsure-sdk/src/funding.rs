//! r-cash funding and payment-carrying writes.
//!
//! The devnet's native REV vault funds a fresh purse; the purse withdraws a payment and
//! the payment is handed to one r-sure arm in the same deploy. The UI never sees a private
//! capability.

use rsure_core::{ComponentKey, PROJECT_TERM_BUDGET};

use crate::error::{Result, SdkError};
use crate::wire::Write;
use crate::Client;

fn check(term: &str) -> Result<()> {
    if term.len() > PROJECT_TERM_BUDGET {
        return Err(SdkError::TermTooLarge {
            bytes: term.len(),
            budget: PROJECT_TERM_BUDGET,
        });
    }
    Ok(())
}

fn fund_term(payments: &str, amount: i64) -> String {
    format!(
        r#"new rl(`rho:registry:lookup`), paymentsCh, accountCh, facetCh,
    ertpCh, issuerCh, purseCh, fundCh, wdCh, depCh,
    deployerId(`rho:rchain:deployerId`), deployId(`rho:rchain:deployId`) in {{
  rl!(`{payments}`, *paymentsCh) |
  for (Payments <- paymentsCh) {{
    Payments!("ensureAccount", *deployerId, *accountCh) |
    for (@a <- accountCh) {{
      match a {{
        (true, account, ownerId) => {{
          @account!("depositFacet", "REV", *facetCh) |
          for (@fr <- facetCh) {{
            match fr {{
              (true, facet) => {{
                rl!(`rho:rchain:ertp`, *ertpCh) |
                for (@(_, ERTP) <- ertpCh) {{
                  @ERTP!("getRevIssuer", *issuerCh) |
                  for (@(revBrand, revIssuer) <- issuerCh) {{
                    @revIssuer!("makeEmptyPurse", *purseCh) |
                    for (@(true, purse) <- purseCh) {{
                      @purse!("revFund", *deployerId, {amount}, *fundCh) |
                      for (@_ <- fundCh) {{
                        @purse!("withdraw", (revBrand, {amount}), *wdCh) |
                        for (@(true, payment) <- wdCh) {{
                          @facet!("deposit", payment, *depCh) |
                          for (@d <- depCh) {{
                            match d {{
                              (true, balance) => {{ deployId!((true, ownerId, balance)) }}
                              _ => {{ deployId!(d) }}
                            }}
                          }}
                        }}
                      }}
                    }}
                  }}
                }}
              }}
              _ => {{ deployId!(fr) }}
            }}
          }}
        }}
        _ => {{ deployId!(a) }}
      }}
    }}
  }}
}}"#
    )
}

fn payment_term(
    payments: &str,
    target: &str,
    arm: &str,
    before: &str,
    after: &str,
    amount: i64,
) -> String {
    format!(
        r#"new rl(`rho:registry:lookup`), paymentsCh, issuerCh, purseCh,
    fundCh, wdCh, targetCh, resultCh,
    deployerId(`rho:rchain:deployerId`), deployId(`rho:rchain:deployId`) in {{
  rl!(`{payments}`, *paymentsCh) |
  for (Payments <- paymentsCh) {{
    Payments!("issuer", "REV", *issuerCh) |
    for (@(true, brand, issuer) <- issuerCh) {{
      @issuer!("makeEmptyPurse", *purseCh) |
      for (@(true, purse) <- purseCh) {{
        @purse!("revFund", *deployerId, {amount}, *fundCh) |
        for (@_ <- fundCh) {{
          @purse!("withdraw", (brand, {amount}), *wdCh) |
          for (@(true, payment) <- wdCh) {{
            rl!(`{target}`, *targetCh) |
            for (Target <- targetCh) {{
              Target!("{arm}", {before}payment{after}, *resultCh) |
              for (@r <- resultCh) {{ deployId!(r) }}
            }}
          }}
        }}
      }}
    }}
  }}
}}"#
    )
}

impl Client {
    /// Move native REV from the signer's vault into the signer's r-cash account.
    pub async fn fund_account_rev(&self, amount: i64) -> Result<Write<serde_json::Value>> {
        if amount < 1 {
            return Err(SdkError::refused("amount"));
        }
        let payments = self.manifest().component_uri(ComponentKey::Payments);
        let term = fund_term(payments, amount);
        check(&term)?;
        self.deploy_term(&term).await
    }

    async fn payment_call(
        &self,
        target: &str,
        arm: &str,
        before_payment: &[String],
        after_payment: &[String],
        amount: i64,
    ) -> Result<Write<serde_json::Value>> {
        if amount < 1 {
            return Err(SdkError::refused("amount"));
        }
        let payments = self.manifest().component_uri(ComponentKey::Payments);
        let before = if before_payment.is_empty() {
            String::new()
        } else {
            format!("{}, ", before_payment.join(", "))
        };
        let after = if after_payment.is_empty() {
            String::new()
        } else {
            format!(", {}", after_payment.join(", "))
        };
        let term = payment_term(payments, target, arm, &before, &after, amount);
        check(&term)?;
        self.deploy_term(&term).await
    }

    pub async fn slip_fund_premium(
        &self,
        slip_uri: &str,
        amount: i64,
    ) -> Result<Write<serde_json::Value>> {
        self.payment_call(
            slip_uri,
            "fundPremium",
            &["*deployerId".into()],
            &[],
            amount,
        )
        .await
    }

    pub async fn syndicate_contribute(
        &self,
        syndicate_uri: &str,
        amount: i64,
    ) -> Result<Write<serde_json::Value>> {
        self.payment_call(
            syndicate_uri,
            "contribute",
            &["*deployerId".into()],
            &[],
            amount,
        )
        .await
    }

    pub async fn fund_contribute(
        &self,
        fund_uri: &str,
        amount: i64,
        policy_id: &str,
    ) -> Result<Write<serde_json::Value>> {
        let policy = rsure_core::render::quote_str(policy_id)?;
        self.payment_call(fund_uri, "contribute", &[], &[policy], amount)
            .await
    }
}

#[cfg(test)]
mod tests {
    use super::{fund_term, payment_term};
    use std::collections::BTreeSet;

    /// Every `*name` used in the term must be declared by the top-level `new`. A missing
    /// binder is a free variable, and the node refuses such a term at parse time.
    fn assert_channels_bound(term: &str) {
        let binders = term
            .strip_prefix("new ")
            .and_then(|rest| rest.split_once(" in {"))
            .map(|(head, _)| head)
            .expect("the term must open with a top-level new");
        let bound: BTreeSet<&str> = binders
            .split(',')
            .map(|item| item.trim().split('(').next().unwrap_or(""))
            .collect();
        for (index, _) in term.match_indices('*') {
            let name: String = term[index + 1..]
                .chars()
                .take_while(|ch| ch.is_ascii_alphanumeric() || *ch == '_')
                .collect();
            assert!(!name.is_empty(), "stray * in the term");
            assert!(
                bound.contains(name.as_str()),
                "{name} is used but not bound by new: {binders}"
            );
        }
    }

    #[test]
    fn funding_term_binds_the_withdraw_channel() {
        for amount in [1, 1_000, 20_000] {
            let term = fund_term("rho:id:payments", amount);
            assert!(
                term.contains("fundCh, wdCh, depCh"),
                "wdCh binder is missing"
            );
            assert!(term.contains(&format!(", {amount}, *fundCh")));
            assert!(term.contains(&format!("(revBrand, {amount}), *wdCh")));
            assert_channels_bound(&term);
        }
    }

    #[test]
    fn payment_term_binds_every_channel() {
        let term = payment_term(
            "rho:id:payments",
            "rho:id:slip",
            "fundPremium",
            "*deployerId, ",
            "",
            1_000,
        );
        assert!(term.contains("fundCh, wdCh, targetCh"));
        assert!(term.contains("Target!(\"fundPremium\", *deployerId, payment, *resultCh)"));
        assert_channels_bound(&term);
    }
}
