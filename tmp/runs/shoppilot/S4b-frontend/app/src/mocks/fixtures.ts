import type {
  CheckoutQuote,
  OrderDetail,
  OrderSummaryItem,
  SessionUser,
} from '../api/types.gen';

/* Deterministic offline fixtures. No PII that maps to a real person. */

export const DEMO_USER: SessionUser = {
  user_id: 'usr_demo_0001',
  display_name: 'Test Customer',
  email_masked: 'c••••••••@shoppilot.test',
};

export const DEMO_CART_ID = 'cart_demo_0001';

export const DEMO_QUOTE: CheckoutQuote = {
  cart_id: DEMO_CART_ID,
  subtotal: { amount_minor: 45000, currency: 'THB' },
  discount: { amount_minor: 5000, currency: 'THB' },
  shipping: { amount_minor: 4000, currency: 'THB' },
  total: { amount_minor: 44000, currency: 'THB' },
};

export const DEMO_ORDER_NO = 'SP-2026-000042';

export const DEMO_ORDERS: OrderSummaryItem[] = [
  {
    order_no: DEMO_ORDER_NO,
    status: 'SHIPPED',
    total: { amount_minor: 44000, currency: 'THB' },
    placed_at: '2026-06-01T03:00:00.000Z',
  },
  {
    order_no: 'SP-2026-000041',
    status: 'DELIVERED',
    total: { amount_minor: 12900, currency: 'THB' },
    placed_at: '2026-05-20T03:00:00.000Z',
  },
];

export const DEMO_ORDER_DETAIL: OrderDetail = {
  order_no: DEMO_ORDER_NO,
  status: 'SHIPPED',
  total: { amount_minor: 44000, currency: 'THB' },
  placed_at: '2026-06-01T03:00:00.000Z',
  shipping_address: '99/1 Sukhumvit Rd, Khlong Toei, Bangkok 10110',
  customer_email: 'customer+test@shoppilot.test',
  customer_phone: '0812345678',
  tracking_no: 'TH-TRK-7788',
  timeline: [
    { status: 'AWAITING_PAYMENT', at: '2026-06-01T03:00:00.000Z' },
    { status: 'PAID', at: '2026-06-01T03:05:00.000Z' },
    { status: 'PACKING', at: '2026-06-01T06:00:00.000Z' },
    { status: 'SHIPPED', at: '2026-06-02T01:00:00.000Z' },
  ],
};
