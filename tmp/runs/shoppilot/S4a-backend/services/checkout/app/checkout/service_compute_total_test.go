package checkout

import (
	"testing"

	"github.com/stretchr/testify/require"
)

func TestComputeTotal(t *testing.T) {
	cases := []struct {
		name     string
		subtotal int
		discount int
		shipping int
		want     int
	}{
		{"plain subtotal plus shipping, no discount", 10000, 0, 500, 10500},
		{"discount applied", 10000, 2000, 500, 8500},
		{"zero everything", 0, 0, 0, 0},
		{"discount equal to subtotal floors merchandise at zero, shipping remains", 10000, 10000, 500, 500},
		{"discount larger than subtotal is clamped, never negative", 10000, 99999, 500, 500},
		{"no shipping", 7500, 1000, 0, 6500},
		{"negative subtotal treated as zero", -100, 0, 500, 500},
		{"negative shipping treated as zero", 10000, 0, -500, 10000},
		{"negative discount treated as zero (no free money to the merchant either)", 10000, -2000, 500, 10500},
		{"discount exactly equals subtotal", 5000, 5000, 0, 0},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			require.Equal(t, tc.want, computeTotal(tc.subtotal, tc.discount, tc.shipping))
		})
	}
}
