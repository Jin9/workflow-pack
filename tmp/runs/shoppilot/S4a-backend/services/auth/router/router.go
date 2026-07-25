package router

import (
	"time"

	"gitlab.com/example-org/platform/backend/common/app"
	commonconfig "gitlab.com/example-org/platform/backend/common/config"
	"gitlab.com/example-org/platform/backend/common/health"
	"gitlab.com/example-org/platform/backend/common/middleware"

	authdomain "gitlab.com/example-org/platform/backend/auth/app/auth"
	"gitlab.com/example-org/platform/backend/auth/app/auth/access"

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
	registerAuthRoutes(r, d)
}

// registerAuthRoutes wires the auth domain HTTP routes, constructing the domain
// handler from the shared infrastructure clients in Deps.
func registerAuthRoutes(r *gin.Engine, d Deps) {
	fs := d.firestoreClient.Inner()
	h := authdomain.NewHandler(authdomain.HandlerConfig{
		CredentialStorage:  access.NewCredentialStorage(fs),
		TokenFamilyStorage: access.NewTokenFamilyStorage(fs),
		AuditStorage:       access.NewAuditStorage(fs),
		Token:              d.token,
		Hash:               d.hash,
		Issuer:             d.cfg.JWT.Issuer,
		Audience:           d.cfg.JWT.Audience,
	})

	g := r.Group("/api/v1/platform/auth")
	g.POST("/login", h.Login)
	g.POST("/refresh", h.Refresh)
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
