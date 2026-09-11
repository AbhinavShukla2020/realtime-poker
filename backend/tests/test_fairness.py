from app.fairness import FairShuffle, commitment, verify_reveal


def test_same_inputs_produce_same_deck():
    first = FairShuffle("hand-1", "server-secret", {"p1": "one", "p2": "two"})
    second = FairShuffle("hand-1", "server-secret", {"p2": "two", "p1": "one"})
    assert first.deal() == second.deal()


def test_reveal_verifies_observed_prefix():
    shuffle = FairShuffle("hand-2", "secret", {"p1": "entropy"})
    observed = [str(card) for card in shuffle.deal()[:12]]
    assert verify_reveal(shuffle.reveal(), observed)


def test_changed_secret_fails_verification():
    shuffle = FairShuffle("hand-3", "secret")
    reveal = shuffle.reveal()
    reveal["server_secret"] = "tampered"
    assert not verify_reveal(reveal, [str(card) for card in shuffle.deal()[:5]])


def test_commitment_is_sha256_hex():
    assert len(commitment("value")) == 64

