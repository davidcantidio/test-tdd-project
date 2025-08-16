from __future__ import annotations

"""Secrets management with environment variables and vault support."""

import os
from enum import Enum
from typing import Any, Dict, Optional


class SecretType(str, Enum):
    """Types of secrets supported."""

    DATABASE_URL = "DATABASE_URL"
    API_KEYS = "API_KEYS"
    ENCRYPTION_KEYS = "ENCRYPTION_KEYS"
    OAUTH_SECRETS = "OAUTH_SECRETS"


class VaultIntegration:
    """Simple in-memory vault integration simulation."""

    def __init__(self) -> None:
        self._cache: Dict[SecretType, Any] = {}

    def connect_to_vault(self) -> bool:
        return True

    def retrieve_secrets(self) -> Dict[SecretType, Any]:
        secrets = {
            SecretType.DATABASE_URL: "vault-db-url",
            SecretType.API_KEYS: {"service": "vault-key"},
            SecretType.ENCRYPTION_KEYS: "vault-encryption-key",
            SecretType.OAUTH_SECRETS: {"client_id": "vault-client"},
        }
        self.cache_secrets(secrets)
        return secrets

    def cache_secrets(self, secrets: Dict[SecretType, Any]) -> None:
        self._cache.update(secrets)

    def get_cached(self, secret_type: SecretType) -> Any:
        return self._cache.get(secret_type)


class SecretsManager:
    """Manage application secrets from env vars or vault."""

    def __init__(self, vault: VaultIntegration | None = None) -> None:
        self.vault = vault or VaultIntegration()
        self._secrets: Dict[SecretType, Any] = {}

    def load_from_env_vars(self) -> Dict[SecretType, Any]:
        for secret in SecretType:
            if secret.value in os.environ:
                self._secrets[secret] = os.environ[secret.value]
        return self._secrets

    def load_from_vault(self) -> Dict[SecretType, Any]:
        if self.vault.connect_to_vault():
            secrets = self.vault.retrieve_secrets()
            self._secrets.update(secrets)
            return secrets
        return {}

    def get_secret(self, secret_type: SecretType) -> Optional[Any]:
        return self._secrets.get(secret_type)

    def rotate_secrets(self) -> Dict[SecretType, Any]:
        rotated = {secret: f"rotated-{secret.value.lower()}" for secret in SecretType}
        self._secrets.update(rotated)
        self.vault.cache_secrets(rotated)
        return rotated

    def validate_secrets(self) -> bool:
        missing = [s.value for s in SecretType if s not in self._secrets]
        if missing:
            raise ValueError(f"Missing secrets: {', '.join(missing)}")
        return True

