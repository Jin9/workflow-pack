/*
 * Analytics — emits one event per user-significant action. Matches
 * frontend-artifacts.json audit_events_emitted exactly:
 *   checkout.confirm.clicked | payment.submitted | order.viewed | login.submitted
 * No PII is ever placed in an event payload.
 */
export type AnalyticsEvent =
  | 'checkout.confirm.clicked'
  | 'payment.submitted'
  | 'order.viewed'
  | 'login.submitted';

type AnalyticsSink = (event: AnalyticsEvent, props?: Readonly<Record<string, string>>) => void;

let sink: AnalyticsSink = () => {
  /* default no-op; a real transport is wired by the host app. */
};

export function setAnalyticsSink(next: AnalyticsSink): void {
  sink = next;
}

export function track(event: AnalyticsEvent, props?: Readonly<Record<string, string>>): void {
  sink(event, props);
}
