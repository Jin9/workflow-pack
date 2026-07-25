package router

import (
	"context"
	"database/sql"
	"log/slog"
	"net/http"
	"strings"

	"gitlab.com/example-org/platform/backend/common/crypt"
	"gitlab.com/example-org/platform/backend/common/database"
	commonfirestore "gitlab.com/example-org/platform/backend/common/firestore"
	"gitlab.com/example-org/platform/backend/common/hash"
	"gitlab.com/example-org/platform/backend/common/httpclient"
	"gitlab.com/example-org/platform/backend/common/kafka"
	"gitlab.com/example-org/platform/backend/common/middleware"
	commonredis "gitlab.com/example-org/platform/backend/common/redis"
	"gitlab.com/example-org/platform/backend/common/token"

	"gitlab.com/example-org/platform/backend/inventory/config"

	"github.com/redis/go-redis/v9"
)

// Deps holds all shared infrastructure clients for the application.
// Initialized once in main and passed to both HTTP and subscriber wiring.
type Deps struct {
	cfg             config.Config
	httpClient      *http.Client
	firestoreClient *commonfirestore.Client
	mysqlClient     *sql.DB
	redisClient     redis.UniversalClient
	producer        kafka.Producer
	hash            hash.HashManager
	cipher          crypt.Cipher
	token           token.JWTSigner
}

// NewDeps constructs all infrastructure clients from config.
// The returned cleanup func must be deferred by the caller.
func NewDeps(ctx context.Context, cfg config.Config) (Deps, func()) {
	httpClient := httpclient.NewHTTPClient(middleware.ForwardRefIDOption, httpclient.DebugOption(cfg.HttpClient.EnableLogDebug))
	fs := commonfirestore.MustNewClient(ctx, newFirestoreConfig(cfg))
	db := database.MustNewMySQLWithConfig(newMySQLConfig(cfg))
	rdb := commonredis.MustNew(cfg.Redis.Addr, cfg.Redis.Password)
	producer := newProducer(cfg)

	d := Deps{
		cfg:             cfg,
		httpClient:      httpClient,
		firestoreClient: fs,
		mysqlClient:     db,
		redisClient:     rdb,
		hash:            newHashManager(cfg),
		cipher:          newCipher(cfg),
		token:           newTokenManager(cfg),
		producer:        producer,
	}

	cleanup := func() {
		_ = fs.Close()
		_ = db.Close()
		_ = rdb.Close()
		_ = producer.Close()
	}

	return d, cleanup
}

func newMySQLConfig(cfg config.Config) database.MySQLConfig {
	return database.MySQLConfig{
		Host:     cfg.MySQL.Host,
		Port:     cfg.MySQL.Port,
		User:     cfg.MySQL.User,
		Password: cfg.MySQL.Password,
		DBName:   cfg.MySQL.DBName,
	}
}

func newTokenManager(cfg config.Config) token.JWTSigner {
	return token.MustNewJWTSigner(token.JWTSignerConfig{
		PrivateKey: cfg.JWT.PrivateKey,
		Alg:        string(token.ES256),
		Issuer:     cfg.JWT.Issuer,
		Audience:   cfg.JWT.Audience,
		Expire:     cfg.JWT.ExpDuration,
	})
}

func newHashManager(cfg config.Config) hash.HashManager {
	return hash.MustNewHashManager(hash.HashManagerCfgs{
		Pepper: cfg.Hash.Pepper,
	})
}

func newCipher(cfg config.Config) crypt.Cipher {
	return crypt.MustNew(crypt.Config{
		Key: cfg.Aesgcm.Key,
	})
}

func newFirestoreConfig(cfg config.Config) commonfirestore.Config {
	return commonfirestore.Config{
		ProjectID:       cfg.Firestore.ProjectID,
		CredentialsJSON: []byte(cfg.Firestore.CredentialsJSON),
		DatabaseID:      cfg.Firestore.DatabaseID,
		ConnectTimeout:  cfg.Firestore.ConnectTimeout,
	}
}

// newProducer creates a Kafka producer with env-aware logging.
// Returns nil when KAFKA_PRODUCER_BROKERS is empty (producer is optional).
func newProducer(cfg config.Config) kafka.Producer {
	brokers := strings.TrimSpace(cfg.Producer.Brokers)
	if brokers == "" {
		slog.Info("kafka producer skipped (KAFKA_PRODUCER_BROKERS is empty)")
		return nil
	}

	producer := kafka.MustNewProducer(kafka.ProducerConfig{
		KafkaConf: kafka.NewSyncProducerGuarantee(),
		Brokers:   splitCSV(brokers),
	})

	return kafka.WithLoggingFromEnv(producer, cfg.Producer.Env)
}

func splitCSV(value string) []string {
	parts := strings.Split(value, ",")
	filtered := make([]string, 0, len(parts))
	for _, part := range parts {
		trimmed := strings.TrimSpace(part)
		if trimmed != "" {
			filtered = append(filtered, trimmed)
		}
	}
	return filtered
}
