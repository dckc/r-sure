# Bind a policy

> **Status:** Mapping only.

`Slip.bind` is permissionless once the insured has accepted, the premium is funded and the
shares sum to 10000. It is atomic:

1. For each subscription, `Syndicate.openLine` consumes the `LineGrant` using the slip's
   private token, moves capacity from committed to written, and returns line capabilities.
2. `LineFactory.create` captures the credit, pay and release capabilities plus the policy
   token.
3. `PolicyFactory.create` stores the line URIs and the coverage terms and holds the premium
   purse.
4. `Policy.distribute` pays the broker commission, the central fund levy and each line's
   premium share, then marks the policy distributed.

If any step fails, the whole deploy rolls back; a partially bound policy is not possible.
