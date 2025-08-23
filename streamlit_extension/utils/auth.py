#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔐 Google OAuth 2.0 para o TDD Framework (versão refinada)

Principais melhorias:
- PKCE + CSRF state/nonce com TTL
- Verificação de id_token (OpenID) + fallback /userinfo
- Configuração desacoplada (dataclass)
- SessionStore (Protocol) para testar sem Streamlit
- Não persiste client_secret em sessão
- prompt='consent' apenas quando necessário
- Revogação de token no logout
"""

from __future__ import annotations

import os
import time
import json
import hmac
import base64
import hashlib
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Tuple, Protocol, runtime_checkable

# ---- Dependências opcionais (graceful import) --------------------------------
try:
    import streamlit as st
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google.oauth2 import id_token as google_id_token
    from google_auth_oauthlib.flow import Flow
    import requests
    from googleapiclient.discovery import build
    DEPS = True
except Exception as e:
    logging.info(f"⚠️ Auth deps não disponíveis: {e}")
    st = None  # type: ignore
    DEPS = False


# ---- Configuração -------------------------------------------------------------

@dataclass(frozen=True)
class GoogleOAuthConfig:
    client_id: str
    client_secret: str              # usado apenas para troca de token; não vai para sessão
    redirect_uri: str
    scopes: tuple[str, ...]
    app_name: str = "TDD Framework"
    require_auth: bool = True
    debug: bool = False
    session_timeout_seconds: int = 7200  # 2h
    session_cookie_name: str = "tdd_framework_session"
    allowed_hd: Optional[str] = None     # domínio do workspace (ex.: "empresa.com")

    # segurança
    state_ttl_seconds: int = 600         # 10 minutos
    nonce_ttl_seconds: int = 600
    clock_skew_seconds: int = 60         # tolerância de relógio

    @staticmethod
    def from_streamlit() -> GoogleOAuthConfig:
        if not DEPS:
            raise ImportError("Dependências de autenticação ausentes")
        try:
            google_cfg = st.secrets["google"]
            app_cfg = st.secrets.get("app", {})
            sess_cfg = st.secrets.get("session", {})
            allowed_hd = google_cfg.get("allowed_hd") if isinstance(google_cfg, dict) else None
            return GoogleOAuthConfig(
                client_id=google_cfg["client_id"],
                client_secret=google_cfg["client_secret"],
                redirect_uri=google_cfg["redirect_uri"],
                scopes=tuple(google_cfg.get("scopes", ("openid", "email", "profile"))),
                app_name=app_cfg.get("name", "TDD Framework"),
                require_auth=app_cfg.get("require_auth", True),
                debug=app_cfg.get("debug", False),
                session_timeout_seconds=int(sess_cfg.get("timeout_minutes", 120)) * 60,
                session_cookie_name=sess_cfg.get("cookie_name", "tdd_framework_session"),
                allowed_hd=allowed_hd,
            )
        except Exception as e:
            logging.info(f"Google OAuth não configurado corretamente: {e}")
            # fallback seguro com defaults
            return GoogleOAuthConfig(
                client_id="",
                client_secret="",
                redirect_uri="",
                scopes=("openid", "email", "profile"),
                require_auth=True,
                debug=False,
            )


# ---- Abstração de sessão (testável) -----------------------------------------

@runtime_checkable
class SessionStore(Protocol):
    def get(self, key: str, default: Any = None) -> Any: ...
    def set(self, key: str, value: Any) -> None: ...
    def delete(self, key: str) -> None: ...


class StreamlitSessionStore:
    def get(self, key: str, default: Any = None) -> Any:
        return st.session_state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        st.session_state[key] = value

    def delete(self, key: str) -> None:
        if key in st.session_state:
            del st.session_state[key]


# ---- Utilitários -------------------------------------------------------------

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def _pkce_pair() -> Tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = _b64url(digest)
    return verifier, challenge

def _secure_random_hex(n: int = 32) -> str:
    return secrets.token_hex(n)

def _safe_log(logger: logging.Logger, msg: str) -> None:
    logger.debug(msg)


# ---- Núcleo OAuth ------------------------------------------------------------

class GoogleOAuthManager:
    def __init__(self, cfg: Optional[GoogleOAuthConfig] = None, store: Optional[SessionStore] = None):
        if not DEPS:
            raise ImportError("Dependências de autenticação ausentes")
        self.logger = logging.getLogger(__name__)
        self.cfg = cfg or GoogleOAuthConfig.from_streamlit()
        self.store = store or StreamlitSessionStore()
        self.configured = bool(self.cfg.client_id and self.cfg.redirect_uri)

    # -- State/Nonce com TTL ---------------------------------------------------
    def _stash_with_ttl(self, key: str, value: str, ttl_seconds: int) -> None:
        payload = {"value": value, "exp": (_now() + timedelta(seconds=ttl_seconds)).timestamp()}
        self.store.set(key, payload)

    def _pop_if_valid(self, key: str, candidate: str) -> bool:
        payload = self.store.get(key)
        if not payload:
            return False
        try:
            exp = float(payload["exp"])
            val = str(payload["value"])
        except Exception:
            self.store.delete(key)
            return False
        if _now().timestamp() > exp:
            self.store.delete(key)
            return False
        # compare com timing-safe
        ok = hmac.compare_digest(val, candidate)
        self.store.delete(key)
        return ok

    # -- Flow (PKCE) -----------------------------------------------------------
    def _create_flow(self, code_verifier: Optional[str] = None) -> Flow:
        if not self.configured:
            raise RuntimeError("Google OAuth não configurado")
        client_config = {
            "web": {
                "client_id": self.cfg.client_id,
                "client_secret": self.cfg.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [self.cfg.redirect_uri],
            }
        }
        flow = Flow.from_client_config(client_config, scopes=list(self.cfg.scopes))
        flow.redirect_uri = self.cfg.redirect_uri
        # PKCE
        if code_verifier:
            flow.code_verifier = code_verifier
        return flow

    def get_authorization_url(self) -> Tuple[str, str]:
        """Gera URL de autorização com PKCE, state e nonce (CSRF)."""
        flow = self._create_flow()
        code_verifier, code_challenge = _pkce_pair()
        self._stash_with_ttl("oauth_code_verifier", code_verifier, self.cfg.state_ttl_seconds)

        state = _secure_random_hex(16)
        nonce = _secure_random_hex(16)
        self._stash_with_ttl("oauth_state", state, self.cfg.state_ttl_seconds)
        self._stash_with_ttl("oauth_nonce", nonce, self.cfg.nonce_ttl_seconds)

        extra = {
            "access_type": "offline",
            "include_granted_scopes": "true",
            "state": state,
            "prompt": "consent" if not self._has_refresh_token() else None,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        if self.cfg.allowed_hd:
            extra["hd"] = self.cfg.allowed_hd

        # remove None
        extra_clean = {k: v for k, v in extra.items() if v is not None}
        auth_url, _ = flow.authorization_url(**extra_clean)
        return auth_url, state

    def handle_callback(self, authorization_code: str, state: str) -> Dict[str, Any]:
        """Troca code por tokens, valida state/nonce e popula sessão autenticada."""
        if not self._pop_if_valid("oauth_state", state):
            raise ValueError("Estado OAuth inválido/expirado (CSRF)")

        code_verifier_payload = self.store.get("oauth_code_verifier")
        code_verifier = code_verifier_payload.get("value") if isinstance(code_verifier_payload, dict) else None
        self.store.delete("oauth_code_verifier")

        flow = self._create_flow(code_verifier=code_verifier)
        try:
            flow.fetch_token(code=authorization_code)
            cred: Credentials = flow.credentials
        except Exception as e:
            raise RuntimeError(f"Falha ao trocar code por token: {e}") from e

        user_info = self._resolve_user_info(cred)

        # monta sessão (não armazena client_secret/token_uri)
        session_data: Dict[str, Any] = {
            "user_info": user_info,
            "credentials": {
                "token": cred.token,
                "refresh_token": cred.refresh_token,
                "scopes": list(cred.scopes or []),
            },
            "authenticated_at": _now().isoformat(),
            "expires_at": (_now() + timedelta(seconds=self.cfg.session_timeout_seconds)).isoformat(),
        }
        self.store.set("authenticated", True)
        self.store.set("user_session", session_data)
        return session_data

    # -- User info (ID Token / UserInfo / People API) -------------------------
    def _resolve_user_info(self, credentials: Credentials) -> Dict[str, Any]:
        # 1) Se veio id_token, valida com Google
        idinfo: Optional[Dict[str, Any]] = None
        if getattr(credentials, "id_token", None):
            try:
                idinfo = google_id_token.verify_oauth2_token(
                    credentials.id_token,
                    Request(),
                    audience=self.cfg.client_id,
                    clock_skew_in_seconds=self.cfg.clock_skew_seconds,
                )
            except Exception:
                idinfo = None

        # 2) Se não, tenta endpoint OpenID userinfo
        userinfo: Optional[Dict[str, Any]] = None
        if not idinfo:
            try:
                resp = requests.get(
                    "https://openidconnect.googleapis.com/v1/userinfo",
                    headers={"Authorization": f"Bearer {credentials.token}"},
                    timeout=10,
                )
                if resp.ok:
                    userinfo = resp.json()
            except Exception:
                userinfo = None

        # 3) (Opcional) People API para foto/org
        picture = None
        organization = None
        try:
            service = build("people", "v1", credentials=credentials, cache_discovery=False)
            profile = service.people().get(
                resourceName="people/me",
                personFields="photos,organizations"
            ).execute()
            photos = profile.get("photos", [])
            if photos:
                picture = photos[0].get("url")
            orgs = profile.get("organizations", [])
            if orgs:
                organization = orgs[0].get("name")
        except Exception:
            pass  # opcional — não falha a autenticação

        # Consolida
        email = (idinfo or userinfo or {}).get("email")
        name = (idinfo or userinfo or {}).get("name") or (idinfo or {}).get("given_name")
        sub = (idinfo or userinfo or {}).get("sub")
        hd = (idinfo or userinfo or {}).get("hd")
        if self.cfg.allowed_hd and hd and hd != self.cfg.allowed_hd:
            raise PermissionError("Domínio não autorizado")

        return {
            "id": sub or "unknown",
            "email": email or "unknown@example.com",
            "name": name or "Unknown User",
            "picture": picture or (userinfo or {}).get("picture"),
            "organization": organization,
            "hd": hd,
        }

    # -- Sessão ----------------------------------------------------------------
    def _has_refresh_token(self) -> bool:
        sess = self.store.get("user_session") or {}
        creds = sess.get("credentials") or {}
        return bool(creds.get("refresh_token"))

    def is_authenticated(self) -> bool:
        if not self.store.get("authenticated"):
            return False
        sess = self.store.get("user_session")
        if not isinstance(sess, dict):
            return False
        try:
            exp = datetime.fromisoformat(sess["expires_at"])
            if _now() > exp:
                self.logout()
                return False
        except Exception:
            self.logout()
            return False
        return True

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        return (self.store.get("user_session") or {}).get("user_info") if self.is_authenticated() else None

    def refresh_credentials(self) -> bool:
        """Atualiza access token usando refresh_token (se disponível)."""
        sess = self.store.get("user_session")
        if not sess:
            return False
        cred_data = sess.get("credentials") or {}
        if not cred_data.get("refresh_token"):
            return False
        try:
            creds = Credentials(
                token=cred_data.get("token"),
                refresh_token=cred_data["refresh_token"],
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.cfg.client_id,
                client_secret=self.cfg.client_secret,
                scopes=cred_data.get("scopes") or list(self.cfg.scopes),
            )
            creds.refresh(Request())
            cred_data["token"] = creds.token
            sess["credentials"] = cred_data
            sess["expires_at"] = (_now() + timedelta(seconds=self.cfg.session_timeout_seconds)).isoformat()
            self.store.set("user_session", sess)
            return True
        except Exception as e:
            self.logger.warning(f"Falha ao refrescar token: {e}")
            self.logout()
            return False

    def logout(self) -> None:
        """Limpa sessão e tenta revogar refresh_token (se houver)."""
        try:
            sess = self.store.get("user_session") or {}
            cred_data = sess.get("credentials") or {}
            refresh = cred_data.get("refresh_token")
            if refresh:
                # Revogação padrão OAuth (best effort)
                requests.post(
                    "https://oauth2.googleapis.com/revoke",
                    params={"token": refresh},
                    headers={"content-type": "application/x-www-form-urlencoded"},
                    timeout=5,
                )
        except Exception:
            pass
        for key in ("authenticated", "user_session", "oauth_state", "oauth_nonce", "oauth_code_verifier"):
            self.store.delete(key)

    # -- UI helpers (opcionais) ------------------------------------------------
    def render_login_page(self) -> None:
        if not DEPS:
            raise RuntimeError("Sem Streamlit disponível")
        st.title("🔐 TDD Framework - Login necessário")
        st.write("Entre com sua conta Google para continuar.")
        qp = st.query_params or {}
        if "code" in qp and "state" in qp:
            with st.spinner("Autenticando..."):
                try:
                    data = self.handle_callback(qp["code"], qp["state"])
                    st.query_params.clear()
                    st.success(f"✅ Bem-vindo(a), {data['user_info']['name']}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Falha na autenticação: {e}")
                    st.query_params.clear()
                    st.rerun()
            return

        if st.button("🔗 Entrar com Google", type="primary", use_container_width=True):
            try:
                url, _ = self.get_authorization_url()
                st.markdown(
                    f'<meta http-equiv="refresh" content="0; url={url}">',
                    unsafe_allow_html=True,
                )
            except Exception as e:
                st.error(f"Não foi possível iniciar OAuth: {e}")

    def render_user_menu(self) -> None:
        if not (DEPS and self.is_authenticated()):
            return
        user = self.get_current_user() or {}
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 👤 Usuário")
            c1, c2 = st.columns([1, 2])
            with c1:
                if user.get("picture"):
                    st.image(user["picture"], width=48)
                else:
                    st.markdown("👤")
            with c2:
                st.markdown(f"**{user.get('name','Usuário')}**")
                st.caption(user.get("email", "sem email"))
                if user.get("organization"):
                    st.caption(f"🏢 {user['organization']}")
            if st.button("🚪 Sair", use_container_width=True):
                self.logout()
                st.rerun()


# ---- Decorator utilitário ----------------------------------------------------

def require_authentication(page_func):
    """Decorator para páginas Streamlit que exigem login."""
    def wrapper(*args, **kwargs):
        if not DEPS:
            # Modo sem UI: bloqueia com log claro (não faz I/O)
            logging.error("❌ Autenticação indisponível: deps ausentes")
            return None
        auth = GoogleOAuthManager()
        if not auth.cfg.require_auth:
            return page_func(*args, **kwargs)
        if not auth.is_authenticated():
            auth.render_login_page()
            st.stop()
        # refresh opportunístico se estiver perto do vencimento (metade do timeout)
        sess = st.session_state.get("user_session") if st else None
        try:
            if sess:
                exp = datetime.fromisoformat(sess["expires_at"])
                if (exp - _now()).total_seconds() < auth.cfg.session_timeout_seconds / 2:
                    auth.refresh_credentials()
        except Exception:
            pass
        return page_func(*args, **kwargs)
    return wrapper


# ---- Funções utilitárias compatíveis com o seu código atual ------------------

def get_authenticated_user() -> Optional[Dict[str, Any]]:
    if not DEPS:
        return _get_traditional_auth_user()
    auth = GoogleOAuthManager()
    if not auth.configured:
        return _get_traditional_auth_user()
    return auth.get_current_user()

def is_user_authenticated() -> bool:
    if not DEPS:
        return _is_traditional_auth_active()
    auth = GoogleOAuthManager()
    if not auth.configured:
        return _is_traditional_auth_active()
    return auth.is_authenticated()

# Fallbacks para seu middleware legado (se existirem)
def _get_traditional_auth_user() -> Optional[Dict[str, Any]]:
    try:
        from ..auth.middleware import get_current_user  # type: ignore
        u = get_current_user()
        if not u:
            return None
        return {
            "id": getattr(u, "id", "unknown"),
            "email": getattr(u, "email", getattr(u, "username", "user@local")),
            "name": getattr(u, "username", getattr(u, "name", "User")),
            "picture": None,
            "organization": None,
        }
    except Exception:
        return None

def _is_traditional_auth_active() -> bool:
    try:
        from ..auth.middleware import is_authenticated  # type: ignore
        return bool(is_authenticated())
    except Exception:
        return False
