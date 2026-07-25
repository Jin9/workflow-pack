package router

import (
	"time"

	"gitlab.com/example-org/platform/backend/common/app"
	commonconfig "gitlab.com/example-org/platform/backend/common/config"
	"gitlab.com/example-org/platform/backend/common/health"
	"gitlab.com/example-org/platform/backend/common/middleware"

	checkoutdomain "gitlab.com/example-org/platform/backend/checkout/app/checkout"
	"gitlab.com/example-org/platform/backend/checkout/app/checkout/access"

	"github.com/gin-gonic/gin"
)

// Cross-service gateway base URLs. The inventory and order services are reached
// over HTTP only (never by importing their Go packages); the mock PSP needs none.
const (
	inventoryBaseURL = "http://inventory"
	orderBaseURL     = "http://order"
)

// New constructs a gin.Engine with routes and middleware configured.
func New(d Deps, version, commit string, timeoutDuration time.Duration) *gin.Engine {
	r := gin.New()
	r.Use(gin.Recovery())

	if commonconfig.IsLocalEnv() {
		r.Use(gin.Logger())
	}

	r.GET("/liveness", health.Liveness(version, commit))
	r.GET("/metrics", health.Metrics())
	r.GET("/readiness", health.Readiness())

	r.Use(
		middleware.SecurityHeaders(),
		middleware.AccessControl(d.cfg.AccessControl.AllowOrigin, allowedHeaders(d.cfg.Header.RefIDHeaderKey)),
		middleware.TraceContextTraceIDMiddleware(""),
		middleware.RefIDMiddleware(d.cfg.Header.RefIDHeaderKey),
		middleware.AutoLoggingMiddleware(app.CodeSuccess),
		middleware.Timeout(timeoutDuration),
		middleware.AccessLog(),
	)

	registerRoutes(r, d)

	return r
}

// registerRoutes is the hook for wiring domain HTTP routes.
// Add register<Domain>Routes(r, d) calls here as new aggregates are created under /app.
func registerRoutes(r *gin.Engine, d Deps) {
	registerCheckoutRoutes(r, d)
}

// registerCheckoutRoutes wires the checkout domain HTTP routes, constructing the
// domain handler from the shared infrastructure clients in Deps. Firestore-backed
// storages use d.firestoreClient.Inner(); cross-service gateways use d.httpClient.
func registerCheckoutRoutes(r *gin.Engine, d Deps) {
	fs := d.firestoreClient.Inner()
	h := checkoutdomain.NewHandler(checkoutdomain.HandlerConfig{
		CartStorage:        access.NewCartStorage(fs),
		IdempotencyStorage: access.NewIdempotencyStorage(fs),
		CouponStorage:      access.NewCouponStorage(fs),
		CaptureStorage:     access.NewCaptureStorage(fs),
		OutboxStorage:      access.NewOutboxStorage(fs),
		AuditStorage:       access.NewAuditStorage(fs),
		InventoryClient:    access.NewInventoryClient(d.httpClient, inventoryBaseURL),
		OrderClient:        access.NewOrderClient(d.httpClient, orderBaseURL),
		PSPClient:          access.NewPSPClient(),
	})

	g := r.Group("/api/v1/platform/checkout")
	g.POST("/confirm", h.Confirm)
	g.POST("/capture", h.Capture)
}

func allowedHeaders(refIDHeaderKey string) []string {
	return []string{
		"Content-Type",
		"Content-Length",
		"Accept-Encoding",
		"X-CSRF-Token",
		"Authorization",
		"accept",
		"origin",
		"Cache-Control",
		"X-Requested-With",
		refIDHeaderKey,
	}
}
