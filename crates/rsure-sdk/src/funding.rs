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

impl Client {
    /// Move native REV from the signer's vault into the signer's r-cash account.
    pub async fn fund_account_rev(&self, amount: i64) -> Result<Write<serde_json::Value>> {
        if amount < 1 {
            return Err(SdkError::refused("amount"));
        }
        let payments = self.manifest().component_uri(ComponentKey::Payments);
        let term = format!(
            r#"new rl(`rho:registry:lookup`), paymentsCh, accountCh, facetCh,
    ertpCh, issuerCh, purseCh, fundCh, depCh,
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
        );
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
        let term = format!(
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
        );
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
