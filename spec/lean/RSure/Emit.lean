import RSure.Basic
import RSure.Model.Math
import RSure.Model.Types
import RSure.Model.Syndicate
import RSure.Model.Grant
import RSure.Model.Slip
import RSure.Model.Line
import RSure.Model.Distribution
import RSure.Model.Policy
import RSure.Model.Fund
import RSure.Model.Books
import RSure.Model.Claim

open RSure
open RSure.Model.Math
open RSure.Model.Types

namespace RSure.Emit

def syn (cap com wr : Nat) : Model.Syndicate.SyndicateState :=
  { capital := cap, committed := com, written := wr, premiums := 0, claimsPaid := 0,
    nonce := 0, status := SyndicateStatus.active }

def showSyn : Option Model.Syndicate.SyndicateState → String
  | none => "none"
  | some s => s!"ok:{s.capital},{s.committed},{s.written},{Model.Syndicate.free s}"

def args (exposure : Nat) : Model.Syndicate.QuoteArgs :=
  { manager := true, classOk := true, shareBps := 5000, exposure := exposure,
    expiryHeight := 100, nowHeight := 1 }

def line (exp paid : Nat) : Model.Line.LineState :=
  { exposure := exp, paid := paid, credited := 0, paidFor := [], nonce := 0,
    status := LineStatus.bound }

def showLine : Option Model.Line.LineState → String
  | none => "none"
  | some s =>
      let st := match s.status with
        | LineStatus.bound => "bound"
        | LineStatus.released => "released"
      s!"ok:{s.paid},{st}"

def slip (prem funded : Nat) (shares : List Nat) : Model.Slip.SlipState :=
  { premiumTotal := prem, funded := funded, shares := shares, insured := 1,
    insuredAccepted := true, status := SlipStatus.subscribed, nonce := 0 }

def showSlip : Option Model.Slip.SlipState → String
  | none => "none"
  | some s =>
      let st := match s.status with
        | SlipStatus.open => "open"
        | SlipStatus.subscribed => "subscribed"
        | SlipStatus.bound => "bound"
        | SlipStatus.expired => "expired"
      s!"ok:{st}"

def dist (base : Nat) (bps : List Nat) : Model.Distribution.DistributionState :=
  { base := base, plan := Model.Distribution.buildPlan base bps,
    status := DistributionStatus.planned, nonce := 0 }

def showDist : Option Model.Distribution.DistributionState → String
  | none => "none"
  | some s =>
      let st := match s.status with
        | DistributionStatus.planned => "planned"
        | DistributionStatus.paid => "paid"
      s!"ok:{st}"

def pol (remaining perClaim deductible : Nat) : Model.Policy.PolicyState :=
  { premiumTotal := 1000, brokerBps := 1000, fundBps := 500, lineBps := [5000, 5000],
    aggregateLimit := 1000, aggregatePaid := 0, aggregateRemaining := remaining,
    perClaimLimit := perClaim, deductible := deductible, distributed := false,
    settledClaims := [], status := PolicyStatus.active, nonce := 0 }

def showPolicy : Option Model.Policy.PolicyState → String
  | none => "none"
  | some s => s!"ok:{s.aggregateRemaining}"

def fund (bal cap : Nat) : Model.Fund.FundState :=
  { balance := bal, maxCover := cap, covers := [], contributions := [], admins := 3,
    threshold := 2, nonce := 0, govNonce := 0 }

def showFund : Option (Model.Fund.FundState × Nat) → String
  | none => "none"
  | some (s, paid) => s!"ok:{paid},{s.balance}"

def claimStd (lead : Nat) (second : Nat) : Model.Claim.ClaimState :=
  { kind := some Model.Claim.ClaimKind.standard, status := ClaimStatus.notified,
    leadManager := lead, secondManager := second, agreedAmount := 0, claimedAmount := 1000,
    assessmentAmount := 0, assessmentPresent := false, leadAgreed := false,
    secondAgreed := false, oracleCase := none, appliedCase := none, paid := 0 }

def claimComplex : Model.Claim.ClaimState :=
  { kind := some Model.Claim.ClaimKind.complex, status := ClaimStatus.classified,
    leadManager := 1, secondManager := 2, agreedAmount := 0, claimedAmount := 1000,
    assessmentAmount := 0, assessmentPresent := false, leadAgreed := false,
    secondAgreed := false, oracleCase := none, appliedCase := none, paid := 0 }

def showClaim : Option Model.Claim.ClaimState → String
  | none => "none"
  | some s =>
      let st := match s.status with
        | ClaimStatus.notified => "notified"
        | ClaimStatus.classified => "classified"
        | ClaimStatus.assessed => "assessed"
        | ClaimStatus.assessing => "assessing"
        | ClaimStatus.agreed => "agreed"
        | ClaimStatus.disputed => "disputed"
        | ClaimStatus.upheld => "upheld"
        | ClaimStatus.partiallyUpheld => "partially_upheld"
        | ClaimStatus.denied => "denied"
        | ClaimStatus.settled => "settled"
        | ClaimStatus.closed => "closed"
      s!"ok:{st},{s.agreedAmount}"

def showBook : Option Model.Books.Book → String
  | none => "none"
  | some _ => "ok"

def main : IO Unit := do
  IO.println s!"math.share.half|1000,5000|{share 1000 5000}"
  IO.println s!"math.share.full|1000,10000|{share 1000 10000}"
  IO.println s!"math.share.trunc|999,3333|{share 999 3333}"
  let p := premiumSplit 1000 1000 500
  IO.println s!"math.split.conserve|1000,1000,500|{p.commission},{p.levy},{p.net}"
  IO.println s!"math.payable.cap|1000,800,900,100|{payable 1000 800 900 100}"
  IO.println s!"math.payable.deduct|1000,800,900,900|{payable 1000 800 900 900}"
  IO.println s!"math.payable.aggregate|1000,2000,600,0|{payable 1000 2000 600 0}"
  IO.println s!"math.payable.aggregate-third|1000,800,600,0|{payable 1000 800 600 0}"
  IO.println s!"math.alloc.sum|1000,[5000,5000]|{sumNat (alloc 1000 [5000,5000])}"
  IO.println s!"math.alloc.remainder|1001,[3333,3333,3334]|{sumNat (alloc 1001 [3333,3333,3334])}"
  IO.println s!"synd.quote.free|1000,0,0,400|{showSyn (Model.Syndicate.quote (syn 1000 0 0) (args 400))}"
  IO.println s!"synd.quote.over|1000,0,0,1200|{showSyn (Model.Syndicate.quote (syn 1000 0 0) (args 1200))}"
  IO.println s!"synd.openLine|1000,400,0,400|{showSyn (Model.Syndicate.openLine (syn 1000 400 0) 400 true)}"
  IO.println s!"synd.pay.free|1000,0,400,100|{showSyn (Model.Syndicate.payLoss (syn 1000 0 400) 100)}"
  IO.println s!"synd.release.restore|1000,0,400|{showSyn (Model.Syndicate.release (syn 1000 0 400) 400 0)}"
  let g := Model.Grant.consume { status := GrantStatus.open } true true
  let g2 := match g with
    | none => none
    | some g' => Model.Grant.consume g' true true
  IO.println s!"grant.consume.once|open|{match g2 with | none => "none" | some _ => "consumed"}"
  IO.println s!"slip.bind.subscribed|[5000,5000]|{showSlip (Model.Slip.bind (slip 100 100 [5000,5000]))}"
  IO.println s!"slip.bind.under|[5000,4000]|{showSlip (Model.Slip.bind (slip 100 100 [5000,4000]))}"
  IO.println s!"slip.bind.unfunded|100,90|{showSlip (Model.Slip.bind (slip 100 90 [5000,5000]))}"
  IO.println s!"slip.expire.refund|funded=100|{match Model.Slip.expire (slip 100 100 [5000,5000]) true with | none => "none" | some (_, credit) => toString credit}"
  let paidOnce := Model.Line.pay (line 500 0) 7 100 true
  IO.println s!"line.pay.once|claim=7|{match paidOnce with | none => "none" | some s' => showLine (Model.Line.pay s' 7 100 true)}"
  IO.println s!"line.pay.bound|exposure=500,amount=600|{showLine (Model.Line.pay (line 500 0) 7 600 true)}"
  IO.println s!"distribution.run.sum|1000,[4000,6000]|{Model.Distribution.sumPlan (Model.Distribution.buildPlan 1000 [4000,6000])}"
  IO.println s!"distribution.run.twice|planned|{match Model.Distribution.run (dist 1000 [4000,6000]) with | none => "none" | some s' => showDist (Model.Distribution.run s')}"
  IO.println s!"policy.settle.aggregate|remaining=1000,payable=700|{showPolicy (Model.Policy.settleClaim (pol 1000 800 100) 7 1000)}"
  IO.println s!"policy.settle.aggregate-third|remaining=600,payable=500|{showPolicy (Model.Policy.settleClaim (pol 600 800 100) 7 1000)}"
  IO.println s!"fund.cover.cap|amount=600,max=500|{showFund (Model.Fund.cover (fund 1000 500) 7 600 1 2)}"
  let cov := Model.Fund.cover (fund 1000 500) 7 100 1 2
  IO.println s!"fund.cover.once|claim=7|{match cov with | none => "none" | some (s', _) => showFund (Model.Fund.cover s' 7 100 2 2)}"
  IO.println s!"claim.standard.lead|caller=1,lead=1|{showClaim (Model.Claim.agree (claimStd 1 2) { caller := 1, amount := 500, basisHash := 0 })}"
  IO.println s!"claim.complex.second-first|caller=2|{showClaim (Model.Claim.agree claimComplex { caller := 2, amount := 500, basisHash := 0 })}"
  let disputed := { claimComplex with oracleCase := some 5 }
  IO.println s!"claim.apply.partial-bound|amount=1200,claimed=1000|{showClaim (Model.Claim.applyDecision disputed 5 Model.Claim.DecisionOutcome.partiallyUpheld 1200)}"
  IO.println s!"claim.terminal.refused|settled|{showClaim (Model.Claim.agree (Model.Claim.settledStandardClaim) { caller := 1, amount := 999, basisHash := 0 })}"
  let b := Model.Books.register { entries := [] } 1 10
  IO.println s!"book.register.twice|id=1|{match b with | none => "none" | some b' => showBook (Model.Books.register b' 1 20)}"

end RSure.Emit

def main : IO Unit := RSure.Emit.main

#eval main
