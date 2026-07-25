package auth

import (
	"time"

	"gitlab.com/example-org/platform/backend/common/hash"
	"gitlab.com/example-org/platform/backend/common/token"

	"gitlab.com/example-org/platform/backend/auth/app/auth/access"
)

const (
	accessTokenTTL  = 15 * time.Minute
	refreshTokenTTL = 14 * 24 * time.Hour
)

// HandlerConfig is the dependency set for the auth domain, wired from the
// composition root (router/deps.go) in router/router.go's registerAuthRoutes.
type HandlerConfig struct {
	CredentialStorage  access.CredentialStorage
	TokenFamilyStorage access.TokenFamilyStorage
	AuditStorage       access.AuditStorage
	Token              token.JWTSigner
	Hash               hash.HashManager
	Issuer             string
	Audience           string
}

type handler struct {
	credentialStorage  access.CredentialStorage
	tokenFamilyStorage access.TokenFamilyStorage
	auditStorage       access.AuditStorage
	token              token.JWTSigner
	hash               hash.HashManager
	issuer             string
	audience           string
	now                func() time.Time
}

// NewHandler builds the auth domain handler from its dependencies.
func NewHandler(cfg HandlerConfig) *handler {
	return &handler{
		credentialStorage:  cfg.CredentialStorage,
		tokenFamilyStorage: cfg.TokenFamilyStorage,
		auditStorage:       cfg.AuditStorage,
		token:              cfg.Token,
		hash:               cfg.Hash,
		issuer:             cfg.Issuer,
		audience:           cfg.Audience,
		now:                func() time.Time { return time.Now().UTC() },
	}
}
