package router

import (
	"time"

	"gitlab.com/example-org/platform/backend/common/app"
	commonconfig "gitlab.com/example-org/platform/backend/common/config"
	"gitlab.com/example-org/platform/backend/common/health"
	"gitlab.com/example-org/platform/backend/common/middleware"

	inventorydomain "gitlab.com/example-org/platform/backend/inventory/app/inventory"
	"gitlab.com/example-org/platform/backend/inventory/app/inventory/access"

	"github.com/gin-gonic/gin"
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
	registerInventoryRoutes(r, d)
}

// registerInventoryRoutes wires the inventory domain HTTP routes, constructing
// the domain handler from the shared infrastructure clients in Deps. Stock lives
// in MySQL (the ADR-002 atomic conditional decrement); reservations and the audit
// trail live in Firestore.
func registerInventoryRoutes(r *gin.Engine, d Deps) {
	fs := d.firestoreClient.Inner()
	h := inventorydomain.NewHandler(inventorydomain.HandlerConfig{
		StockStorage:       access.NewStockStorage(d.mysqlClient),
		ReservationStorage: access.NewReservationStorage(fs),
		AuditStorage:       access.NewAuditStorage(fs),
	})

	g := r.Group("/api/v1/platform/inventory")
	g.POST("/reserve", h.Reserve)
	g.POST("/release", h.Release)
	g.POST("/adjust", h.Adjust)
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
