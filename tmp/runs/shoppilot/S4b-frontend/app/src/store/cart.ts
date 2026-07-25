import { create } from 'zustand';

/*
 * Cart — CLIENT-owned state (state_ownership.cart = "client", Zustand).
 *
 * The cart holds line items and a cart_id. It deliberately does NOT hold a total:
 * the checkout total is server-computed (state_ownership.computed_total = derived
 * from the server). Cart mutations MAY be optimistic; money paths never are.
 */
export interface CartLine {
  sku: string;
  name: string;
  qty: number;
}

interface CartState {
  cartId: string;
  lines: CartLine[];
  addLine: (line: CartLine) => void;
  removeLine: (sku: string) => void;
  clear: () => void;
  itemCount: () => number;
}

export const useCartStore = create<CartState>((set, get) => ({
  // Deterministic demo cart id (offline MSW fixtures key off it).
  cartId: 'cart_demo_0001',
  lines: [
    { sku: 'SKU-NOTE-01', name: 'Notebook A5', qty: 1 },
    { sku: 'SKU-PEN-02', name: 'Gel pen (pack of 3)', qty: 2 },
  ],
  addLine: (line) =>
    set((state) => {
      const existing = state.lines.find((l) => l.sku === line.sku);
      if (existing !== undefined) {
        return {
          lines: state.lines.map((l) =>
            l.sku === line.sku ? { ...l, qty: l.qty + line.qty } : l,
          ),
        };
      }
      return { lines: [...state.lines, line] };
    }),
  removeLine: (sku) =>
    set((state) => ({ lines: state.lines.filter((l) => l.sku !== sku) })),
  clear: () => set({ lines: [] }),
  itemCount: () => get().lines.reduce((sum, l) => sum + l.qty, 0),
}));
