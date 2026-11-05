use crate::error::CoreError;

/// Split `amount` across `shares` (basis points). The last share absorbs the remainder.
pub fn split_bps(amount: u64, shares: &[u16]) -> Result<Vec<u64>, CoreError> {
    if shares.is_empty() {
        return Err(CoreError::Shares);
    }
    let sum: u32 = shares.iter().map(|bps| *bps as u32).sum();
    if sum != 10_000 {
        return Err(CoreError::Shares);
    }
    let mut out = Vec::with_capacity(shares.len());
    let mut paid: u64 = 0;
    for (index, bps) in shares.iter().enumerate() {
        if index + 1 == shares.len() {
            out.push(amount.checked_sub(paid).ok_or(CoreError::Shares)?);
        } else {
            let part = u64::try_from((amount as u128) * (*bps as u128) / 10_000)
                .map_err(|_| CoreError::Amount)?;
            paid = paid.checked_add(part).ok_or(CoreError::Amount)?;
            out.push(part);
        }
    }
    Ok(out)
}

/// Commission, central-fund levy and net premium.
pub fn premium_split(
    premium_total: u64,
    broker_bps: u16,
    fund_bps: u16,
) -> Result<(u64, u64, u64), CoreError> {
    if broker_bps > 10_000 || fund_bps > 10_000 || broker_bps as u32 + fund_bps as u32 > 10_000 {
        return Err(CoreError::BasisPoints);
    }
    let commission = u64::try_from((premium_total as u128) * (broker_bps as u128) / 10_000)
        .map_err(|_| CoreError::Amount)?;
    let fund = u64::try_from((premium_total as u128) * (fund_bps as u128) / 10_000)
        .map_err(|_| CoreError::Amount)?;
    let net = premium_total
        .checked_sub(commission)
        .and_then(|value| value.checked_sub(fund))
        .ok_or(CoreError::Amount)?;
    Ok((commission, fund, net))
}

/// `max(0, min(agreed, per_claim, remaining) - deductible)`.
pub fn payable(
    agreed: u64,
    per_claim_limit: u64,
    aggregate_remaining: u64,
    deductible: u64,
) -> Result<u64, CoreError> {
    if per_claim_limit == 0 || aggregate_remaining == 0 {
        return Ok(0);
    }
    let cap = agreed.min(per_claim_limit).min(aggregate_remaining);
    Ok(cap.saturating_sub(deductible))
}

/// Split net premium across line shares, with the last line absorbing the remainder.
pub fn line_shares(net_premium: u64, shares: &[u16]) -> Result<Vec<u64>, CoreError> {
    split_bps(net_premium, shares)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn premium_is_conserved() -> Result<(), CoreError> {
        let (commission, fund, net) = premium_split(10_000, 1_500, 250)?;
        assert_eq!(commission, 1_500);
        assert_eq!(fund, 250);
        assert_eq!(commission + fund + net, 10_000);
        Ok(())
    }

    #[test]
    fn last_line_absorbs_remainder() -> Result<(), CoreError> {
        let parts = line_shares(100, &[3_333, 3_333, 3_334])?;
        assert_eq!(parts.iter().sum::<u64>(), 100);
        Ok(())
    }

    #[test]
    fn payable_is_capped() -> Result<(), CoreError> {
        assert_eq!(payable(500, 400, 1_000, 50)?, 350);
        assert_eq!(payable(500, 400, 300, 50)?, 250);
        assert_eq!(payable(50, 400, 300, 100)?, 0);
        Ok(())
    }
}
