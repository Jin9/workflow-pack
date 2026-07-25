package main

import (
	"context"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"runtime"
	"runtime/debug"
	"syscall"
	"time"

	commonconfig "gitlab.com/example-org/platform/backend/common/config"
	"gitlab.com/example-org/platform/backend/common/logger"

	"gitlab.com/example-org/platform/backend/order/config"
	"gitlab.com/example-org/platform/backend/order/router"

	_ "embed"
	_ "time/tzdata"
)

const (
	gracefulShutdownDuration = 10 * time.Second
	serverReadHeaderTimeout  = 5 * time.Second
	serverReadTimeout        = 5 * time.Second
	serverWriteTimeout       = 10 * time.Second // request hangup after this durations
	handlerTimeout           = serverWriteTimeout - (time.Millisecond * 100)
)

// go build -ldflags "-X main.commit=123456"
var commit string

//go:embed VERSION
var version string

func init() {
	if os.Getenv("GOMAXPROCS") != "" {
		runtime.GOMAXPROCS(0) // GOMAXPROCS
	} else {
		runtime.GOMAXPROCS(1) // 0 - 999m
	}
	if os.Getenv("GOMEMLIMIT") != "" {
		debug.SetMemoryLimit(-1) // GOMEMLIMIT
	}
}

func main() {
	cfg := config.C(commonconfig.Env)
	_ = logger.New(
		logger.AWSKeyReplacer,
		logger.OpenSearchKeyReplacer,
		logger.CensorReplacer,
	)

	ctx, cancel := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer cancel()

	d, cleanupDeps := router.NewDeps(ctx, cfg)
	defer cleanupDeps()

	consumerDone, stopConsumer := router.StartSubscriber(ctx, d)

	// Orchestrate teardown
	defer func() {
		cancel()
		stopConsumer()
		router.WaitForSubscriber(consumerDone, gracefulShutdownDuration)
	}()

	// Monitor unexpected subscriber exit to trigger global shutdown
	go func() {
		<-consumerDone
		cancel()
	}()

	r := router.New(d, version, commit, handlerTimeout)

	srv := newServer(cfg, r)
	go gracefulShutdown(ctx, srv, gracefulShutdownDuration)

	slog.Info("run", "port", cfg.Server.Port)

	// Safely recover if ListenAndServe panics, ensuring standard exit and teardowns
	defer func() {
		if r := recover(); r != nil {
			slog.Error("HTTP server panicked during runtime", slog.Any("panic", r))
		}
	}()

	if err := srv.ListenAndServe(); err != http.ErrServerClosed {
		slog.Error("HTTP server ListenAndServe", "error", err)
		return
	}

	slog.Info("bye")
}

func newServer(cfg config.Config, handler http.Handler) *http.Server {
	return &http.Server{
		Addr:              ":" + cfg.Server.Port,
		Handler:           handler,
		ReadHeaderTimeout: serverReadHeaderTimeout,
		ReadTimeout:       serverReadTimeout,
		WriteTimeout:      serverWriteTimeout,
		MaxHeaderBytes:    1 << 20,
	}
}

func gracefulShutdown(ctx context.Context, srv *http.Server, timeout time.Duration) {
	<-ctx.Done()

	slog.Info("shutting down", "timeout", timeout.String())
	shutdownCtx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()
	if err := srv.Shutdown(shutdownCtx); err != nil {
		slog.Info("HTTP server Shutdown", "error", err)
	}
}
