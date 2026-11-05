import { describe, expect, it } from "vitest";
import { asMap, shortUri, unwrap } from "./chain";
import { syndicateRole, claimManager } from "./capabilities";
import { networkForNode } from "./network";

describe("chain reply helpers", () => {
  it("unwraps the protocol success tuple", () => {
    expect(unwrap([true, { id: "syn:1" }])).toEqual({ id: "syn:1" });
    expect(unwrap("bare")).toBe("bare");
  });

  it("normalises a missing map to an empty object", () => {
    expect(asMap(undefined)).toEqual({});
    expect(asMap([true, { a: 1 }])).toEqual({ a: 1 });
  });

  it("shortens long ids without hiding the tail", () => {
    expect(shortUri("rho:id:abcdefghijklmnopqrstuvwxyz")).toContain("…");
  });
});

describe("role capabilities", () => {
  const syndicate = { ownerId: "alice", managerId: "bob" };
  it("recognises owner and manager", () => {
    expect(syndicateRole(syndicate, "alice").allowed).toBe(true);
    expect(syndicateRole(syndicate, "bob").allowed).toBe(true);
    expect(syndicateRole(syndicate, "carol").allowed).toBe(false);
    expect(syndicateRole(syndicate, null).reason).toContain("connect");
  });

  it("recognises lead and second claim managers", () => {
    expect(claimManager({ leadManager: "alice" }, "alice").allowed).toBe(true);
    expect(claimManager({ secondManager: "bob" }, "bob").allowed).toBe(true);
    expect(claimManager({ leadManager: "alice" }, "carol").allowed).toBe(false);
  });
});

describe("network presets", () => {
  it("uses the devnet profile for localhost", () => {
    const profile = networkForNode("http://localhost:40403");
    expect(profile.name).toBe("devnet");
    expect(profile.shard).toBe("/root");
  });

  it("uses a custom profile for another host", () => {
    expect(networkForNode("http://10.0.0.5:40403").name).toBe("custom");
  });
});
