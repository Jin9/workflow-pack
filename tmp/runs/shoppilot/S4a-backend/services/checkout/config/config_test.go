package config

import (
	"sync"
	"testing"
)

func TestPrefixEnv(t *testing.T) {
	t.Run("Prefix is empty", func(t *testing.T) {
		prefix := prefix("")

		if prefix != "" {
			t.Error("Expected empty string but got", prefix)
		}
	})

	t.Run("Prefix is not empty", func(t *testing.T) {
		prefix := prefix("LOCAL")

		if prefix != "LOCAL_" {
			t.Error("Expected LOCAL_ but got", prefix)
		}
	})
}

func TestC(t *testing.T) {
	orig := logFatal
	defer func() { logFatal = orig }()

	// Provide valid config fields required by env definitions to avoid premature failures
	// Or we can just let ParseEnv fail but ensure we catch the mocked logFatal!

	t.Run("parse env failure", func(t *testing.T) {
		fatalCalled := false
		logFatal = func(v ...any) { fatalCalled = true }
		
		// Reset sync.Once and state
		once = sync.Once{}
		config = Config{}

		// "PORT" is required (notEmpty). Without setting it, ParseEnv will fail!
		C("TEST_PARSE_FAIL")
		if !fatalCalled {
			t.Error("expected logFatal due to missing mandatory env vars")
		}
	})

	t.Run("base64 jwt private key failure", func(t *testing.T) {
		fatalCalled := false
		logFatal = func(v ...any) { fatalCalled = true }
		
		once = sync.Once{}
		config = Config{}

		// Mock all required fields
		t.Setenv("PORT", "8080")
		t.Setenv("REF_ID_HEADER_KEY", "x-ref")
		t.Setenv("JWT_ISSUER", "iss")
		t.Setenv("JWT_AUDIENCE", "aud")
		t.Setenv("JWT_EXP_DURATION", "1h")
		t.Setenv("SECRET_JWT_PRIVATE_KEY", "invalid-base64!")
		t.Setenv("GCP_PROJECT_ID", "prj")
		t.Setenv("GCP_CREDENTIALS_JSON", "ew==") // valid dummy base64
		t.Setenv("GOOGLE_OAUTH2_VERIFY_TOKEN", "u")
		t.Setenv("GOOGLE_OAUTH2_GET_USER_PROFILE", "u")
		t.Setenv("GOOGLE_OAUTH2_REVOKE_TOKEN", "u")
		t.Setenv("SECRET_AESGCM_KEY", "key")
		t.Setenv("SECRET_HASH_PEPPER", "pepper")

		C("")
		if !fatalCalled {
			t.Error("expected logFatal due to invalid base64 jwt private key")
		}
	})

	t.Run("base64 firestore json failure", func(t *testing.T) {
		fatalCalled := false
		logFatal = func(v ...any) { fatalCalled = true }
		
		once = sync.Once{}
		config = Config{}

		// Mock all required fields
		t.Setenv("PORT", "8080")
		t.Setenv("REF_ID_HEADER_KEY", "x-ref")
		t.Setenv("JWT_ISSUER", "iss")
		t.Setenv("JWT_AUDIENCE", "aud")
		t.Setenv("JWT_EXP_DURATION", "1h")
		t.Setenv("SECRET_JWT_PRIVATE_KEY", "ew==") // valid base64
		t.Setenv("GCP_PROJECT_ID", "prj")
		t.Setenv("GCP_CREDENTIALS_JSON", "invalid-base-64!")
		t.Setenv("GOOGLE_OAUTH2_VERIFY_TOKEN", "u")
		t.Setenv("GOOGLE_OAUTH2_GET_USER_PROFILE", "u")
		t.Setenv("GOOGLE_OAUTH2_REVOKE_TOKEN", "u")
		t.Setenv("SECRET_AESGCM_KEY", "key")
		t.Setenv("SECRET_HASH_PEPPER", "pepper")

		C("")
		if !fatalCalled {
			t.Error("expected logFatal due to invalid base64 firestore json")
		}
	})

	t.Run("success", func(t *testing.T) {
		fatalCalled := false
		logFatal = func(v ...any) { fatalCalled = true } // should not be called
		
		once = sync.Once{}
		config = Config{}

		// Mock all required fields
		t.Setenv("PORT", "8080")
		t.Setenv("REF_ID_HEADER_KEY", "x-ref")
		t.Setenv("JWT_ISSUER", "iss")
		t.Setenv("JWT_AUDIENCE", "aud")
		t.Setenv("JWT_EXP_DURATION", "1h")
		t.Setenv("SECRET_JWT_PRIVATE_KEY", "ew==")
		t.Setenv("GCP_PROJECT_ID", "prj")
		t.Setenv("GCP_CREDENTIALS_JSON", "ew==")
		t.Setenv("GOOGLE_OAUTH2_VERIFY_TOKEN", "u")
		t.Setenv("GOOGLE_OAUTH2_GET_USER_PROFILE", "u")
		t.Setenv("GOOGLE_OAUTH2_REVOKE_TOKEN", "u")
		t.Setenv("SECRET_AESGCM_KEY", "key")
		t.Setenv("SECRET_HASH_PEPPER", "pepper")

		c := C("")
		if fatalCalled {
			t.Error("unexpected logFatal on complete setup")
		}
		if c.Server.Port != "8080" {
			t.Errorf("port not matched, got %v", c.Server.Port)
		}
	})
}
