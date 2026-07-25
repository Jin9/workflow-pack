package checkout

// computeTotal is the single source of truth for an order total, in minor currency
// units. It is PURE (no I/O, no clock) so it is exhaustively unit-tested: the server
// NEVER trusts a client-supplied total. The discount is clamped so it can never make
// the merchandise portion negative, and the result is floored at zero.
func computeTotal(subtotalMinor int, discountMinor int, shippingMinor int) int {
	subtotal := nonNegative(subtotalMinor)
	shipping := nonNegative(shippingMinor)
	discount := nonNegative(discountMinor)

	// A discount can reduce merchandise to zero but never below it; it does not
	// eat into shipping.
	if discount > subtotal {
		discount = subtotal
	}

	return subtotal - discount + shipping
}

func nonNegative(v int) int {
	if v < 0 {
		return 0
	}
	return v
}
