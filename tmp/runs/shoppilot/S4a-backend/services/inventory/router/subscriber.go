package router

import (
	"context"
	"fmt"
	"log/slog"
	"strings"
	"time"

	"gitlab.com/example-org/platform/backend/common/kafka"

	inventorydomain "gitlab.com/example-org/platform/backend/inventory/app/inventory"
	"gitlab.com/example-org/platform/backend/inventory/app/inventory/access"

	"github.com/IBM/sarama"
)

// StartSubscriber starts Kafka consumer group and returns a done channel and stop function for shutdown coordination.
func StartSubscriber(ctx context.Context, d Deps) (<-chan struct{}, func()) {
	done := make(chan struct{})
	if !subscriberConfigured(d) {
		close(done)
		return done, func() {}
	}

	eventHandlers := registerEventRoutes(d)

	consumerCtx, cancel := context.WithCancel(ctx)

	go func() {
		defer close(done)
		defer func() {
			if r := recover(); r != nil {
				slog.Error("subscriber panicked", slog.Any("panic", r))
			}
		}()

		group := newSubscriberGroup(d)
		defer func() {
			if err := group.Close(); err != nil {
				slog.Error("failed to close subscriber group", slog.String("error", err.Error()))
			}
		}()

		if err := runSubscriber(consumerCtx, group, splitCSV(d.cfg.Consumer.Topics), eventHandlers); err != nil {
			slog.Error("subscriber stopped with error", slog.String("error", err.Error()))
		}
	}()

	return done, cancel
}

func newSubscriberGroup(d Deps) sarama.ConsumerGroup {
	return kafka.MustNewConsumerGroup(kafka.ConsumerConfig{
		Brokers:                  splitCSV(d.cfg.Consumer.Brokers),
		GroupID:                  d.cfg.Consumer.GroupID,
		OffsetsInitial:           d.cfg.Consumer.OffsetsInitial,
		RebalanceGroupStrategies: d.cfg.Consumer.RebalanceStrategy,
		KafkaConf:                kafka.NewConsumerConfigAtLeastOnce(),
	})
}

// WaitForSubscriber waits for shutdown completion or times out.
func WaitForSubscriber(done <-chan struct{}, timeout time.Duration) {
	select {
	case <-done:
		return
	case <-time.After(timeout):
		slog.Warn("consumer shutdown timeout", "timeout", timeout.String())
	}
}

func subscriberConfigured(d Deps) bool {
	return strings.TrimSpace(d.cfg.Consumer.Brokers) != "" &&
		strings.TrimSpace(d.cfg.Consumer.GroupID) != "" &&
		strings.TrimSpace(d.cfg.Consumer.Topics) != ""
}

func runSubscriber(ctx context.Context, group sarama.ConsumerGroup, topics []string, eventHandlers map[string]kafka.KafkaHandler) error {
	if len(topics) == 0 {
		return nil
	}

	var processor kafka.Processor
	if len(eventHandlers) > 0 {
		processor = kafka.NewEventRouter(eventHandlers)
	} else {
		processor = kafka.DefaultProcessor
	}

	handler := kafka.NewConsumerGroupHandler(ctx, processor)

	slog.Debug("subscriber started")
	defer slog.Debug("subscriber stopped")

	for {
		if err := group.Consume(ctx, topics, handler); err != nil {
			return err
		}
		if ctx.Err() != nil {
			return nil
		}
	}
}

// registerEventRoutes is the hook for wiring Kafka event→handler routes.
// Add register<Domain>Events(d) calls here and mergeRoutes them as new aggregates are created under /app.
func registerEventRoutes(d Deps) map[string]kafka.KafkaHandler {
	routes := make(map[string]kafka.KafkaHandler)

	mergeRoutes(routes, registerInventoryEvents(d))

	return routes
}

// registerInventoryEvents wires the inventory domain's Kafka consumers. Inventory
// consumes order.status.changed (emitted by the order service) and releases the
// reservation on a cancellation (the SAGA compensation, ADR-004).
func registerInventoryEvents(d Deps) map[string]kafka.KafkaHandler {
	fs := d.firestoreClient.Inner()
	h := inventorydomain.NewHandler(inventorydomain.HandlerConfig{
		StockStorage:       access.NewStockStorage(d.mysqlClient),
		ReservationStorage: access.NewReservationStorage(fs),
		AuditStorage:       access.NewAuditStorage(fs),
	})

	return map[string]kafka.KafkaHandler{
		"order.status.changed": h.OnStatusChanged,
	}
}

// mergeRoutes copies src entries into dst, panicking on duplicate event names
// to catch wiring mistakes at startup rather than at runtime.
func mergeRoutes(dst, src map[string]kafka.KafkaHandler) {
	for event, handler := range src {
		if _, exists := dst[event]; exists {
			panic(fmt.Sprintf("duplicate event route: %s", event))
		}
		dst[event] = handler
	}
}
