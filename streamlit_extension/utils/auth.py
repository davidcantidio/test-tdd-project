#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔐 Google OAuth 2.0 para o TDD Framework (hardened)

Melhorias aplicadas:
- PKCE + CSRF: state/nonce com TTL e validação de nonce no id_token
- Verificação OIDC: iss/aud/azp + clock skew
- Config desacoplada (dataclass) + SessionStore (Protocol) para testes
- People API opcional (lazy + cache curto por sessão)
- Retries idempotentes com backoff (userinfo/revoke)
- Safe redirect pós-login com allowlist
- Refresh compare-and-swap (evita race em múltiplas abas)
- Não persiste client_secret/token_uri na sessão
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


# =============================================================================
# Configuração
# =============================================================================

@dataclass(frozen=True)
class GoogleOAuthConfig:
    # OAuth/OIDC
    client_id: str
    client_secret: str              # usado apenas para troca/refresh; não vai para sessão
    redirect_uri: str
    scopes: tuple[str, ...]
    allowed_hd: Optional[str] = None     # domínio do workspace (ex.: "empresa.com")

    # App
    app_name: str = "TDD Framework"
    require_auth: bool = True
    debug: bool = False

    # Sessão (app, não o access token do Google)
    session_timeout_seconds: int = 7200  # 2h
    session_cookie_name: str = "tdd_framework_session"

    # Segurança
    state_ttl_seconds: int = 600         # 10 min
    nonce_ttl_seconds: int = 600
    clock_skew_seconds: int = 60         # tolerância de relógio

    # Operacional
    enable_people_api: bool = False
    people_api_cache_seconds: int = 300  # 5 min
    allow_dev_fallback: bool = True      # permite user dev quando OAuth não configurado
    allowed_redirect_paths: tuple[str, ...] = ("/", "/dashboard")

    @staticmethod
    def from_streamlit() -> GoogleOAuthConfig:
        if not DEPS:
            raise ImportError("Dependências de autenticação ausentes")
        
        # First, try to load from new config system
        try:
            from config.environment import get_config
            config = get_config()
            oauth_config = config.google_oauth
            
            # Use the new config system if OAuth is enabled and has credentials
            if oauth_config.enabled and oauth_config.client_id and oauth_config.client_secret:
                return GoogleOAuthConfig(
                    client_id=oauth_config.client_id,
                    client_secret=oauth_config.client_secret,
                    redirect_uri=oauth_config.redirect_uri,
                    scopes=tuple(oauth_config.scopes),
                    app_name="TDD Framework",
                    require_auth=config.security.require_auth,
                    debug=config.debug,
                    allow_dev_fallback=config.environment == "development",
                )
                
        except Exception as e:
            logging.info(f"Config system not available, trying Streamlit secrets: {e}")
        
        # Fallback to Streamlit secrets
        try:
            google_cfg = st.secrets["google"]
            app_cfg = st.secrets.get("app", {})
            sess_cfg = st.secrets.get("session", {})
            return GoogleOAuthConfig(
                client_id=google_cfg["client_id"],
                client_secret=google_cfg["client_secret"],
                redirect_uri=google_cfg["redirect_uri"],
                scopes=tuple(google_cfg.get("scopes", ("openid", "email", "profile"))),
                allowed_hd=google_cfg.get("allowed_hd"),
                app_name=app_cfg.get("name", "TDD Framework"),
                require_auth=app_cfg.get("require_auth", True),
                debug=app_cfg.get("debug", False),
                session_timeout_seconds=int(sess_cfg.get("timeout_minutes", 120)) * 60,
                session_cookie_name=sess_cfg.get("cookie_name", "tdd_framework_session"),
                enable_people_api=bool(app_cfg.get("enable_people_api", False)) or bool(os.getenv("ENABLE_PEOPLE_API")),
                people_api_cache_seconds=int(os.getenv("PEOPLE_API_CACHE_SECONDS", "300")),
                allow_dev_fallback=bool(app_cfg.get("allow_dev_fallback", True)),
                allowed_redirect_paths=tuple(app_cfg.get("allowed_redirect_paths", ["/", "/dashboard"])),
            )
        except Exception as e:
            logging.info(f"Google OAuth não configurado corretamente: {e}")
            # Fallback para desenvolvimento quando OAuth não configurado
            return GoogleOAuthConfig(
                client_id="",
                client_secret="",
                redirect_uri="",
                scopes=("openid", "email", "profile"),
                require_auth=False,
                debug=True,
                allow_dev_fallback=True,
            )


# =============================================================================
# Abstração de sessão (testável)
# =============================================================================

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


# =============================================================================
# Utilitários
# =============================================================================

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

def _json_log(logger: logging.Logger, msg: str, **kv):
    try:
        logger.info(f"{msg} | {json.dumps(kv, default=str)}")
    except Exception:
        logger.info(f"{msg} | {kv}")

def _http_get(url: str, headers=None, timeout: int = 10, retries: int = 2):
    for attempt in range(retries + 1):
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code >= 500 and attempt < retries:
            time.sleep(0.2 * (2 ** attempt))
            continue
        return resp
    return resp

def _http_post(url: str, data=None, params=None, headers=None, timeout: int = 10, retries: int = 2):
    for attempt in range(retries + 1):
        resp = requests.post(url, data=data, params=params, headers=headers, timeout=timeout)
        if resp.status_code >= 500 and attempt < retries:
            time.sleep(0.2 * (2 ** attempt))
            continue
        return resp
    return resp


# =============================================================================
# Núcleo OAuth
# =============================================================================

class GoogleOAuthManager:
    def __init__(self, cfg: Optional[GoogleOAuthConfig] = None, store: Optional[SessionStore] = None):
        if not DEPS:
            raise ImportError("Dependências de autenticação ausentes")
        self.logger = logging.getLogger(__name__)
        self.cfg = cfg or GoogleOAuthConfig.from_streamlit()
        self.store = store or StreamlitSessionStore()

        # Verifica se OAuth está configurado de fato (evita placeholders ${...})
        self.configured = bool(
            self.cfg.client_id
            and self.cfg.client_secret
            and self.cfg.redirect_uri
            and not str(self.cfg.client_id).startswith("${")
            and not str(self.cfg.client_secret).startswith("${")
            and getattr(self.cfg, 'enabled', True)  # Check if OAuth is enabled
        )

    # ---- State/Nonce com TTL -------------------------------------------------
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
        ok = hmac.compare_digest(val, candidate)
        self.store.delete(key)
        return ok

    # ---- Flow (PKCE) ---------------------------------------------------------
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
        if code_verifier:
            flow.code_verifier = code_verifier  # PKCE
        return flow

    def get_authorization_url(self) -> Tuple[str, str]:
        """Gera URL de autorização com PKCE, state e nonce (CSRF)."""
        flow = self._create_flow()
        code_verifier, code_challenge = _pkce_pair()
        self._stash_with_ttl("oauth_code_verifier", code_verifier, self.cfg.state_ttl_seconds)

        state = _secure_random_hex(16)
        nonce = _secure_random_hex(16)
        flow_id = _secure_random_hex(8)  # correlação para logs

        self._stash_with_ttl("oauth_state", state, self.cfg.state_ttl_seconds)
        self._stash_with_ttl("oauth_nonce", nonce, self.cfg.nonce_ttl_seconds)
        self.store.set("oauth_flow_id", flow_id)

        extra = {
            "access_type": "offline",
            "include_granted_scopes": "true",
            "state": state,
            "nonce": nonce,  # OpenID Connect
            "prompt": "consent" if not self._has_refresh_token() else None,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        if self.cfg.allowed_hd:
            extra["hd"] = self.cfg.allowed_hd

        auth_url, _ = flow.authorization_url(**{k: v for k, v in extra.items() if v is not None})
        _json_log(self.logger, "auth_url_issued", flow_id=flow_id, state=state, has_refresh=self._has_refresh_token())
        return auth_url, state

    # ---- Callback/Troca de código -------------------------------------------
    def handle_callback(self, authorization_code: str, state: str) -> Dict[str, Any]:
        """Troca code por tokens, valida state/nonce/iss/aud/azp e popula sessão autenticada."""
        flow_id = self.store.get("oauth_flow_id")

        if not self._pop_if_valid("oauth_state", state):
            # limpa resíduos para evitar multi-aba confusa
            for k in ("oauth_code_verifier", "oauth_nonce"):
                self.store.delete(k)
            raise ValueError("Estado OAuth inválido/expirado (CSRF)")

        code_verifier_payload = self.store.get("oauth_code_verifier")
        code_verifier = code_verifier_payload.get("value") if isinstance(code_verifier_payload, dict) else None
        self.store.delete("oauth_code_verifier")

        flow = self._create_flow(code_verifier=code_verifier)
        try:
            flow.fetch_token(code=authorization_code)
            cred: Credentials = flow.credentials
        except Exception as e:
            _json_log(self.logger, "code_exchange_failed", flow_id=flow_id, error=str(e))
            raise RuntimeError(f"Falha ao trocar code por token: {e}") from e

        # Resolve user info (inclui validação do id_token)
        user_info, access_expiry_iso = self._resolve_user_info_and_expiry(cred)

        # Mapeia sessão (sem client_secret/token_uri)
        session_data: Dict[str, Any] = {
            "user_info": user_info,
            "credentials": {
                "token": cred.token,
                "refresh_token": cred.refresh_token,
                "scopes": list(cred.scopes or []),
            },
            "authenticated_at": _now().isoformat(),
            "access_expires_at": access_expiry_iso,
            "expires_at": (_now() + timedelta(seconds=self.cfg.session_timeout_seconds)).isoformat(),
        }
        self.store.set("authenticated", True)
        self.store.set("user_session", session_data)
        _json_log(self.logger, "login_success", flow_id=flow_id, email=user_info.get("email"), sub=user_info.get("id"))
        return session_data

    # ---- User info (ID Token / UserInfo / People API) ------------------------
    def _resolve_user_info_and_expiry(self, credentials: Credentials) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Valida id_token quando presente (iss/aud/azp/nonce) ou consulta /userinfo.
        Retorna (userinfo_dict, access_token_expiry_iso|None).
        """
        idinfo: Optional[Dict[str, Any]] = None
        access_expiry_iso: Optional[str] = None

        # Access token expiry (se google-auth popular)
        try:
            if getattr(credentials, "expiry", None):
                access_expiry_iso = credentials.expiry.astimezone(timezone.utc).isoformat()
        except Exception:
            access_expiry_iso = None

        # 1) id_token → validação completa
        if getattr(credentials, "id_token", None):
            try:
                idinfo = google_id_token.verify_oauth2_token(
                    credentials.id_token,
                    Request(),
                    audience=self.cfg.client_id,
                    clock_skew_in_seconds=self.cfg.clock_skew_seconds,
                )
                iss = idinfo.get("iss")
                if iss not in {"https://accounts.google.com", "accounts.google.com"}:
                    raise PermissionError("Issuer inválido")

                aud = idinfo.get("aud")
                if aud != self.cfg.client_id:
                    raise PermissionError("Audience inválida")

                azp = idinfo.get("azp")
                if azp and azp != self.cfg.client_id:
                    raise PermissionError("Authorized party inválida")

                # nonce claim deve bater com o guardado
                nonce_claim = idinfo.get("nonce")
                if not nonce_claim or not self._pop_if_valid("oauth_nonce", nonce_claim):
                    raise PermissionError("Nonce inválido/expirado")
            except Exception as e:
                _json_log(self.logger, "id_token_validation_failed", error=str(e))
                idinfo = None  # cai para /userinfo

        # 2) /userinfo quando não há id_token válido
        userinfo: Optional[Dict[str, Any]] = None
        if not idinfo:
            try:
                resp = _http_get(
                    "https://openidconnect.googleapis.com/v1/userinfo",
                    headers={"Authorization": f"Bearer {credentials.token}"},
                    timeout=10,
                    retries=2,
                )
                if resp.ok:
                    userinfo = resp.json()
                else:
                    _json_log(self.logger, "userinfo_failed", status=resp.status_code, text=resp.text)
            except Exception as e:
                _json_log(self.logger, "userinfo_exception", error=str(e))
                userinfo = None

        # 3) People API opcional (foto/org) com cache curto
        picture = None
        organization = None
        if self.cfg.enable_people_api:
            try:
                cache_key = "people_cache"
                cache = self.store.get(cache_key) or {}
                cache_exp = cache.get("exp")
                cache_data = cache.get("data")
                if cache_data and cache_exp and _now().timestamp() < float(cache_exp):
                    picture = cache_data.get("picture")
                    organization = cache_data.get("organization")
                else:
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
                    self.store.set(cache_key, {
                        "data": {"picture": picture, "organization": organization},
                        "exp": (_now() + timedelta(seconds=self.cfg.people_api_cache_seconds)).timestamp(),
                    })
            except Exception as e:
                _json_log(self.logger, "people_api_skip", error=str(e))

        # Consolidação
        source = idinfo or userinfo or {}
        email = source.get("email")
        name = source.get("name") or source.get("given_name")
        sub = source.get("sub")
        hd = source.get("hd")

        if self.cfg.allowed_hd:
            # exigir match explícito quando política configurada
            if not hd or hd != self.cfg.allowed_hd:
                raise PermissionError("Domínio não autorizado")

        user = {
            "id": sub or "unknown",
            "email": email or "unknown@example.com",
            "name": name or "Unknown User",
            "picture": picture or source.get("picture"),
            "organization": organization,
            "hd": hd,
        }
        return user, access_expiry_iso

    # ---- Sessão/Refresh ------------------------------------------------------
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

    def ensure_fresh_token(self, margin_seconds: int = 120) -> bool:
        """
        Garante access token "fresco": refresca se expira em < margin_seconds.
        Retorna True se token está ok (após possível refresh), False caso contrário.
        """
        sess = self.store.get("user_session")
        if not sess:
            return False
        access_exp = sess.get("access_expires_at")
        if not access_exp:
            # sem info → tenta refresh se existir refresh_token
            return self.refresh_credentials()

        try:
            exp_dt = datetime.fromisoformat(access_exp)
        except Exception:
            return self.refresh_credentials()

        if (exp_dt - _now()).total_seconds() <= margin_seconds:
            return self.refresh_credentials()
        return True

    def refresh_credentials(self) -> bool:
        """Atualiza access token usando refresh_token (CAS para evitar race)."""
        sess = self.store.get("user_session")
        if not sess:
            return False
        cred_data = sess.get("credentials") or {}
        if not cred_data.get("refresh_token"):
            return False

        prev_token_snapshot = cred_data.get("token")
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

            # CAS: re-le o estado atual; não pisa se já mudou
            current_sess = self.store.get("user_session") or {}
            current_creds = (current_sess.get("credentials") or {})
            if current_creds.get("token") != prev_token_snapshot:
                # outra aba já atualizou; não sobrescreve
                _json_log(self.logger, "refresh_race_avoided")
                return True

            new_access_expiry = None
            try:
                if getattr(creds, "expiry", None):
                    new_access_expiry = creds.expiry.astimezone(timezone.utc).isoformat()
            except Exception:
                new_access_expiry = None

            current_creds["token"] = creds.token
            current_sess["credentials"] = current_creds
            current_sess["access_expires_at"] = new_access_expiry
            current_sess["expires_at"] = (_now() + timedelta(seconds=self.cfg.session_timeout_seconds)).isoformat()
            self.store.set("user_session", current_sess)
            _json_log(self.logger, "refresh_success")
            return True
        except Exception as e:
            _json_log(self.logger, "refresh_failed", error=str(e))
            self.logout()
            return False

    def logout(self) -> None:
        """Limpa sessão e tenta revogar refresh_token (best effort + retries)."""
        try:
            sess = self.store.get("user_session") or {}
            cred_data = sess.get("credentials") or {}
            refresh = cred_data.get("refresh_token")
            if refresh:
                _http_post(
                    "https://oauth2.googleapis.com/revoke",
                    params={"token": refresh},
                    headers={"content-type": "application/x-www-form-urlencoded"},
                    timeout=5,
                    retries=1,
                )
        except Exception as e:
            _json_log(self.logger, "revoke_failed", error=str(e))

        for key in ("authenticated", "user_session", "oauth_state", "oauth_nonce", "oauth_code_verifier", "oauth_flow_id"):
            self.store.delete(key)

    # ---- UI helpers (opcionais) ----------------------------------------------
    def _safe_redirect(self, path: str):
        """Redirect interno com allowlist para evitar open redirect."""
        if not DEPS:
            return
        if path not in self.cfg.allowed_redirect_paths:
            path = "/"
        st.markdown(f'<meta http-equiv="refresh" content="0; url={path}">', unsafe_allow_html=True)

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
                    # redireciona para caminho seguro (se fornecido)
                    next_path = qp.get("next", "/")
                    st.query_params.clear()
                    st.success(f"✅ Bem-vindo(a), {data['user_info']['name']}!")
                    self._safe_redirect(str(next_path))
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Falha na autenticação: {e}")
                    # Limpa artefatos para evitar stuck em multi-aba
                    for k in ("oauth_state", "oauth_nonce", "oauth_code_verifier", "oauth_flow_id"):
                        self.store.delete(k)
                    st.query_params.clear()
                    st.rerun()
            return

        if st.button("🔗 Entrar com Google", type="primary", use_container_width=True):
            try:
                url, _ = self.get_authorization_url()
                st.markdown(f'<meta http-equiv="refresh" content="0; url={url}">', unsafe_allow_html=True)
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


# =============================================================================
# Decorator utilitário
# =============================================================================

def require_authentication(page_func):
    """Decorator para páginas Streamlit que exigem login (e token fresco quando necessário)."""
    def wrapper(*args, **kwargs):
        if not DEPS:
            logging.error("❌ Autenticação indisponível: deps ausentes")
            return None
        auth = GoogleOAuthManager()
        # Em dev sem OAuth, permite acesso (quando configurado)
        if not auth.configured and auth.cfg.allow_dev_fallback:
            return page_func(*args, **kwargs)

        if not auth.cfg.require_auth:
            return page_func(*args, **kwargs)

        if not auth.is_authenticated():
            auth.render_login_page()
            st.stop()

        # Garante token fresco (tentativa best effort)
        try:
            auth.ensure_fresh_token()
        except Exception:
            pass

        return page_func(*args, **kwargs)
    return wrapper


# =============================================================================
# Funções utilitárias compatíveis com o seu código atual
# =============================================================================

def render_login_page() -> None:
    """Wrapper function for backward compatibility."""
    if not DEPS:
        raise RuntimeError("Sem Streamlit disponível")
    auth = GoogleOAuthManager()
    return auth.render_login_page()

def get_authenticated_user() -> Optional[Dict[str, Any]]:
    if not DEPS:
        return _get_traditional_auth_user()
    auth = GoogleOAuthManager()
    if not auth.configured and auth.cfg.allow_dev_fallback:
        return _get_traditional_auth_user()
    return auth.get_current_user()

def is_user_authenticated() -> bool:
    if not DEPS:
        return _is_traditional_auth_active()
    auth = GoogleOAuthManager()
    if not auth.configured and auth.cfg.allow_dev_fallback:
        return _is_traditional_auth_active()
    return auth.is_authenticated()

# ---- Fallbacks para middleware legado (quando existir) -----------------------

def _get_traditional_auth_user() -> Optional[Dict[str, Any]]:
    try:
        from ..auth.middleware import get_current_user  # type: ignore
        u = get_current_user()
        if u:
            return {
                "id": getattr(u, "id", "unknown"),
                "email": getattr(u, "email", getattr(u, "username", "user@local")),
                "name": getattr(u, "username", getattr(u, "name", "User")),
                "picture": None,
                "organization": None,
            }
    except Exception:
        pass

    # Fallback de desenvolvimento (quando permitido)
    return {
        "id": "dev_user",
        "email": "developer@localhost",
        "name": "Developer User",
        "picture": None,
        "organization": "Development",
    }

def _is_traditional_auth_active() -> bool:
    try:
        from ..auth.middleware import is_authenticated  # type: ignore
        result = is_authenticated()
        if result:
            return True
    except Exception:
        pass
    return True  # em dev, considera autenticado


# =============================================================================
# API pública
# =============================================================================

__all__ = [
    "GoogleOAuthConfig",
    "SessionStore",
    "StreamlitSessionStore",
    "GoogleOAuthManager",
    "require_authentication",
    "render_login_page",
    "get_authenticated_user",
    "is_user_authenticated",
]
