package config

import (
	"fmt"
	"log"
	"sync"
	"time"

	"gitlab.com/b2c-e-commerce-platform/platform/backend/common/codec"
	commonconfig "gitlab.com/b2c-e-commerce-platform/platform/backend/common/config"

	env "github.com/caarlos0/env/v11"
)

var logFatal = log.Fatal

// Config holds all environment-based configuration for the application.
// Group related settings into unexported sub-structs (no `env` tag needed on the parent field).
//
// Example:
//
//	type Config struct {
//		...
//		GCP gcp  // no `env` tag needed — nested fields carry their own tags.
//	}
//
//	type gcp struct {
//		ProjectID string `env:"GCP_PROJECT_ID"`
//	}
//
// Flat fields can also be added directly:
//
//	type Config struct {
//		...
//		AppName string `env:"APP_NAME"`
//	}
type Config struct {
	Server        Server
	AccessControl AccessControl
	Firestore     Firestore
	Header        Header
	JWT           JWT
	GoogleClient  GoogleClient
	Aesgcm        Aesgcm
	Hash          Hash
	Consumer      Consumer
	Producer      Producer
	HttpClient    HttpClient
	MySQL         MySQL
	Redis         Redis
}

type Server struct {
	Hostname string `env:"HOSTNAME"`
	Port     string `env:"PORT,notEmpty"`
}

type AccessControl struct {
	AllowOrigin string `env:"ACCESS_CONTROL_ALLOW_ORIGIN"`
}

type Header struct {
	RefIDHeaderKey string `env:"REF_ID_HEADER_KEY,notEmpty"`
}

type JWT struct {
	Issuer      string        `env:"JWT_ISSUER,notEmpty"`
	Audience    string        `env:"JWT_AUDIENCE,notEmpty"`
	ExpDuration time.Duration `env:"JWT_EXP_DURATION,notEmpty"`
	PrivateKey  string        `env:"SECRET_JWT_PRIVATE_KEY,notEmpty"`
}

type Firestore struct {
	ProjectID       string        `env:"GCP_PROJECT_ID,notEmpty"`
	CredentialsJSON string        `env:"GCP_CREDENTIALS_JSON"`
	DatabaseID      string        `env:"GCP_FIRESTORE_DATABASE_ID"`
	ConnectTimeout  time.Duration `env:"GCP_FIRESTORE_CONNECT_TIMEOUT" envDefault:"30s"`
}

type GoogleClient struct {
	VerifyTokenURL    string `env:"GOOGLE_OAUTH2_VERIFY_TOKEN,notEmpty"`
	GetUserProfileURL string `env:"GOOGLE_OAUTH2_GET_USER_PROFILE,notEmpty"`
	RevokeTokenURL    string `env:"GOOGLE_OAUTH2_REVOKE_TOKEN,notEmpty"`
}

type Aesgcm struct {
	Key string `env:"SECRET_AESGCM_KEY,notEmpty"`
}

type Hash struct {
	Pepper string `env:"SECRET_HASH_PEPPER,notEmpty"`
}

type Consumer struct {
	Brokers           string `env:"KAFKA_BROKERS"`
	GroupID           string `env:"KAFKA_GROUP_ID"`
	Topics            string `env:"KAFKA_TOPICS"`
	OffsetsInitial    string `env:"KAFKA_OFFSETS_INITIAL" envDefault:"latest"`
	RebalanceStrategy string `env:"KAFKA_REBALANCE_STRATEGY" envDefault:"range"`
}

type Producer struct {
	Brokers string `env:"KAFKA_PRODUCER_BROKERS"`
	Env     string `env:"ENV" envDefault:"LOCAL"`
}

type HttpClient struct {
	EnableLogDebug bool `env:"HTTP_CLIENT_ENABLE_LOG_DEBUG" envDefault:"false"`
}

type MySQL struct {
	Host     string `env:"MYSQL_HOST"`
	Port     string `env:"MYSQL_PORT"`
	User     string `env:"SECRET_DB_USERNAME"`
	Password string `env:"SECRET_DB_PASSWORD"`
	DBName   string `env:"MYSQL_DATABASE"`
}

type Redis struct {
	Addr     string `env:"REDIS_ADDR"`
	Password string `env:"SECRET_REDIS_PASSWORD"`
}

var once sync.Once
var config Config

func prefix(e string) string {
	if e == "" {
		return ""
	}

	return fmt.Sprintf("%s_", e)
}

func C(envPrefix string) Config {
	once.Do(func() {
		opts := env.Options{
			Prefix: prefix(envPrefix),
		}

		var err error
		config, err = commonconfig.ParseEnv[Config](opts)
		if err != nil {
			logFatal(err)
			return // avoid panic on next line if mocked
		}

		base64Coder := codec.NewBase64Coder()
		rawJWTPrivateKey, err := base64Coder.DecodeBase64(config.JWT.PrivateKey)
		if err != nil {
			logFatal(err)
			return
		}
		config.JWT.PrivateKey = rawJWTPrivateKey

		rawCredentialsJSON, err := base64Coder.DecodeBase64(config.Firestore.CredentialsJSON)
		if err != nil {
			logFatal(err)
			return
		}
		config.Firestore.CredentialsJSON = rawCredentialsJSON

	})

	return config
}
