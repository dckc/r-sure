//! Regression: a normalized `Par` nested beyond prost's default recursion limit must still
//! survive the wire codec used for RSpace continuations.
//!
//! A deploy term with a few dozen nested `for`/`match`/contract layers is valid Rholang and
//! encodes fine, but `prost`'s default decode recursion limit (100) rejected it. That made a
//! valid continuation unreadable on the next proposal, which surfaced as
//! `decode continuation failed — no block was produced`. The parser/normalizer own the depth
//! contract; the wire codec must not impose a second, lower one.

use rchain_models::ast::{New, Par};
use rchain_shared::serialize::Serialize;

#[test]
fn deeply_nested_par_round_trips() {
    // 130 nested `new` nodes: above prost's default decode limit of 100. Built directly so
    // this test is about the codec, not about the parser's own (lower) source-depth bound.
    let mut par = Par::default();
    for _ in 0..130 {
        par = Par {
            news: vec![New {
                p: Box::new(par),
                ..Default::default()
            }],
            ..Default::default()
        };
    }

    let bytes = <Par as Serialize<Par>>::encode(&par);
    let decoded = <Par as Serialize<Par>>::decode(&bytes);
    assert!(
        decoded.is_ok(),
        "decode of {} encoded bytes failed: {:?}",
        bytes.len(),
        decoded.err()
    );
}
