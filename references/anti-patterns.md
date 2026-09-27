# Banned test anti-patterns

Each of these can produce high coverage % while verifying nothing. Reject them
in review; never generate them.

## 1. No assertion at all

```go
// BANNED
func TestCalculateDiscount_Stub(t *testing.T) {
    _, _ = CalculateDiscount(500, Premium)
    _, _ = CalculateDiscount(1500, Premium)
    // every line runs; nothing is checked
}
```

Demonstrated impact: this exact test passed at 84.6% coverage against a
version of `CalculateDiscount` where the premium discount rate was silently
changed from 20% to 0%. The bug shipped clean.

## 2. Circular mock assertion

```go
// BANNED
mockRepo.On("GetPrice").Return(99.0)
result := svc.GetPrice()
assert.Equal(t, 99.0, result) // only proves the mock returns what you told it to
```

Fix: assert on what the *function under test* does with the mocked value —
e.g. that `GetPrice()` applies a markup to the mock's 99.0, not that it
echoes it back unchanged.

## 3. Trivial/identical assertions across table cases

```go
// BANNED
for _, tt := range cases {
    _, err := DoThing(tt.input)
    if err != nil {
        t.Fail() // every case checks the same shallow thing, never the value
    }
}
```

Fix: assert on the actual returned value per case, with the expected value
computed independently (see the working template).

## 4. Weakening the assertion to make the test pass

If a test fails after a code change, the default response is to fix the code
or confirm the new expected value is correct — never to delete/loosen the
assertion so CI goes green. A loosened assertion is functionally identical to
anti-pattern #1.

## 5. Testing the mock instead of the boundary

Heavy mocking of the function under test itself (as opposed to its
dependencies) means you've tested that Go can call a function — not that the
logic is right. Mock dependencies (DB, HTTP clients); never mock the unit
you're actually trying to verify.

## What a compliant test looks like instead

See `references/test-template.go` for the full pattern, but at minimum every
case should look like:

```go
{
    name:         "premium customer over bulk threshold gets tier discount plus $50 bonus",
    price:        1500,
    customerType: Premium,
    wantPrice:    1150, // 1500 - (1500*0.20) - 50   <-- derivation shown, not guessed
    wantErr:      nil,
},
```

The inline comment showing the derivation is not decorative — it's what
proves a human actually worked out the expected value instead of pasting
whatever the function currently returns.
