"""Login and registration page for authentication (hardened)."""

from __future__ import annotations

import os
import re
import hmac
import time
import secrets
import streamlit as st
from typing import Tuple
from .auth_manager import AuthManager
from .user_model import UserRole

# ============================ Config / Flags ============================ #

AUTH_DEBUG = os.environ.get("AUTH_DEBUG", "").lower() in {"1", "true", "yes"}

# Namespacing das chaves de sessão para evitar colisões com outros módulos
SS = st.session_state
K = type("Keys", (), {
    "SESSION_ID": "auth_session_id",
    "CURRENT_USER": "auth_current_user",
    "ATTEMPTS": "auth_login_attempts",
    "LAST_TRY": "auth_last_login_try_ts",
    "ACTIVE_TAB": "auth_active_tab",
    "MODE_SELECT": "auth_mode_selector",
    "START_TS": "auth_session_start_time",
    "EXTENDED": "auth_session_extended",
    "DURATION": "auth_session_duration",
    "CSRF_LOGIN": "auth_csrf_login",
    "CSRF_REG": "auth_csrf_reg",
    # Campos de formulário (limpos após uso)
    "F_LOGIN_USER": "auth_f_login_user",
    "F_LOGIN_PW": "auth_f_login_pw",
    "F_LOGIN_SHOW": "auth_f_login_show",
    "F_LOGIN_REMEMBER": "auth_f_login_remember",
    "F_LOGIN_CSRF": "auth_f_login_csrf",
    "F_REG_USER": "auth_f_reg_user",
    "F_REG_EMAIL": "auth_f_reg_email",
    "F_REG_PW": "auth_f_reg_pw",
    "F_REG_CONFIRM": "auth_f_reg_confirm",
    "F_REG_CSRF": "auth_f_reg_csrf",
})()

# ============================== Helpers ================================ #

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.-]{3,32}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def _safe_msg(prefix: str, exc: Exception) -> str:
    return f"{prefix}: {exc}" if AUTH_DEBUG else prefix

def _password_ok(pw: str) -> Tuple[bool, str, int]:
    """Valida senha e retorna (ok, motivo, score 0-4)."""
    score = 0
    if len(pw) >= 8: score += 1
    if re.search(r"[A-Z]", pw): score += 1
    if re.search(r"[a-z]", pw): score += 1
    if re.search(r"\d", pw): score += 1
    if re.search(r"[^\w\s]", pw): score += 1
    if len(pw) < 8:
        return False, "Password must be at least 8 characters.", score
    if not re.search(r"[A-Za-z]", pw) or not re.search(r"\d", pw):
        return False, "Use letters and numbers to improve password strength.", score
    return True, "", min(score, 4)

# ------------------- CSRF (token de sessão + bind ao form) ------------------- #

def _csrf_get_or_create(key: str) -> str:
    token = SS.get(key)
    if not token:
        token = secrets.token_urlsafe(32)
        SS[key] = token
    return token

def _csrf_check(session_key: str, submitted_token: str) -> bool:
    expected = SS.get(session_key, "")
    # Comparação em tempo constante
    return bool(submitted_token) and hmac.compare_digest(submitted_token, expected)

# ------------------ Rate limit (janela + backoff exponencial) ---------------- #

def _ratelimit_login(max_attempts: int = 5, base_cooldown: int = 30) -> Tuple[bool, str]:
    attempts = int(SS.get(K.ATTEMPTS, 0))
    last_ts = float(SS.get(K.LAST_TRY, 0.0))
    now = time.time()

    # Se passou 10 minutos desde a última tentativa, zera
    if last_ts and (now - last_ts) > 600:
        SS[K.ATTEMPTS] = 0
        attempts = 0

    if attempts >= max_attempts:
        # Backoff exponencial simples: 30s, 60s, 120s, 240s...
        cooldown = base_cooldown * (2 ** (attempts - max_attempts))
        remaining = int(max(0, cooldown - (now - last_ts)))
        if remaining > 0:
            return False, f"Too many attempts. Please wait {remaining}s and try again."
    return True, ""

def _register_attempt(failed: bool) -> None:
    SS[K.LAST_TRY] = time.time()
    if failed:
        SS[K.ATTEMPTS] = int(SS.get(K.ATTEMPTS, 0)) + 1
    else:
        SS[K.ATTEMPTS] = 0  # reset on success

# ---------------------------- Sessão / defaults ----------------------------- #

def _init_session_defaults() -> None:
    SS.setdefault(K.SESSION_ID, None)
    SS.setdefault(K.CURRENT_USER, None)
    SS.setdefault(K.ATTEMPTS, 0)
    SS.setdefault(K.LAST_TRY, 0.0)
    SS.setdefault(K.ACTIVE_TAB, "Login")  # "Login" | "Register"
    _csrf_get_or_create(K.CSRF_LOGIN)
    _csrf_get_or_create(K.CSRF_REG)

def _clear_login_fields():
    for k in (K.F_LOGIN_PW, K.F_LOGIN_SHOW, K.F_LOGIN_USER, K.F_LOGIN_CSRF):
        SS.pop(k, None)

def _clear_register_fields():
    for k in (K.F_REG_USER, K.F_REG_EMAIL, K.F_REG_PW, K.F_REG_CONFIRM, K.F_REG_CSRF):
        SS.pop(k, None)

# ================================ UI ================================= #

def render_login_page():
    """Render login/registration page (com CSRF, RL e limpeza de segredos)."""
    _init_session_defaults()
    st.title("🔐 Authentication")

    # Se já autenticado
    if SS.get(K.CURRENT_USER):
        user = SS[K.CURRENT_USER]
        st.success(f"You're logged in as **{getattr(user, 'username', 'user')}**.")
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("Log out"):
                SS[K.SESSION_ID] = None
                SS[K.CURRENT_USER] = None
                SS.pop(K.START_TS, None)
                SS.pop(K.EXTENDED, None)
                SS.pop(K.DURATION, None)
                _clear_login_fields()
                _clear_register_fields()
                st.toast("Logged out.")
                st.rerun()
        return

    auth_manager = AuthManager()

    # Navegação amigável
    st.markdown("### 🚀 Quick Access")
    active = st.selectbox(
        "Choose action:",
        ["Login", "Register"],
        index=0 if SS.get(K.ACTIVE_TAB, "Login") == "Login" else 1,
        key=K.MODE_SELECT,
        help="Switch between login and registration",
    )
    SS[K.ACTIVE_TAB] = active

    if active == "Login":
        _render_login_form(auth_manager)
    else:
        _render_registration_form(auth_manager)


def _render_login_form(auth_manager: AuthManager):
    st.subheader("Login")

    allowed, msg = _ratelimit_login()
    if not allowed:
        st.error(msg)
        return

    csrf_token = _csrf_get_or_create(K.CSRF_LOGIN)

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", key=K.F_LOGIN_USER)
        # Campo oculto para CSRF (valor exibido oculto)
        st.text_input(
            "csrf",
            key=K.F_LOGIN_CSRF,
            value=csrf_token,
            type="password",
            label_visibility="collapsed",
        )

        pw_col1, pw_col2 = st.columns([4, 1])
        with pw_col1:
            show_pw = st.checkbox("Show password", key=K.F_LOGIN_SHOW, value=False)
        with pw_col2:
            st.empty()

        password = st.text_input(
            "Password",
            type="default" if SS.get(K.F_LOGIN_SHOW) else "password",
            key=K.F_LOGIN_PW,
        )

        col_a, col_b = st.columns([1, 1])
        with col_a:
            remember = st.checkbox("Remember this device", key=K.F_LOGIN_REMEMBER, value=False)
        with col_b:
            if st.link_button("Forgot password?", "#", help="Request password reset"):
                try:
                    if hasattr(auth_manager, "send_password_reset"):
                        auth_manager.send_password_reset((username or "").strip())
                        st.info("If this account exists, a reset message was sent.")
                    else:
                        st.info("Please contact support to reset your password.")
                except Exception as e:
                    st.error(_safe_msg("Password reset unavailable", e))

        submit = st.form_submit_button("Login", type="primary")

    if not submit:
        return

    # CSRF
    if not _csrf_check(K.CSRF_LOGIN, SS.get(K.F_LOGIN_CSRF, "")):
        st.error("Security token invalid. Please try again.")
        _register_attempt(failed=True)
        return

    if not SS.get(K.F_LOGIN_USER) or not SS.get(K.F_LOGIN_PW):
        st.error("Please enter both username and password.")
        _register_attempt(failed=True)
        return

    norm_username = SS[K.F_LOGIN_USER].strip()
    try:
        result = auth_manager.authenticate(norm_username, SS[K.F_LOGIN_PW])
    except Exception as e:
        st.error(_safe_msg("Authentication service unavailable", e))
        _register_attempt(failed=True)
        return

    if getattr(result, "success", False):
        SS[K.SESSION_ID] = result.session_id
        SS[K.CURRENT_USER] = result.user
        SS[K.START_TS] = time.time()

        if remember:
            SS[K.EXTENDED] = True
            SS[K.DURATION] = 7 * 24 * 60 * 60  # 7 days
            session_info = "Your session will last 7 days"
            if hasattr(auth_manager, "issue_persistent_session"):
                try:
                    auth_manager.issue_persistent_session(result.user)
                except Exception as e:
                    if AUTH_DEBUG:
                        st.warning(f"Persistent session not issued: {e}")
        else:
            SS[K.EXTENDED] = False
            SS[K.DURATION] = 2 * 60 * 60  # 2 hours
            session_info = "Your session will last 2 hours"

        _register_attempt(failed=False)
        st.success(f"Welcome back, {result.user.username}!")
        st.info(f"💡 **{session_info}** with gentle reminders before expiring.")
        _clear_login_fields()
        st.rerun()
    else:
        st.error(getattr(result, "message", "Invalid credentials."))
        _register_attempt(failed=True)


def _render_registration_form(auth_manager: AuthManager):
    st.subheader("Register New Account")

    csrf_token = _csrf_get_or_create(K.CSRF_REG)

    with st.form("register_form", clear_on_submit=False):
        username = st.text_input("Username", key=K.F_REG_USER, help="3–32 chars: letters, numbers, . _ -")
        email = st.text_input("Email", key=K.F_REG_EMAIL)
        # Campo oculto para CSRF
        st.text_input(
            "csrf",
            key=K.F_REG_CSRF,
            value=csrf_token,
            type="password",
            label_visibility="collapsed",
        )

        pw_col1, pw_col2 = st.columns([3, 2])
        with pw_col1:
            password = st.text_input("Password", type="password", key=K.F_REG_PW)
        with pw_col2:
            ok_tmp, _, score = _password_ok(SS.get(K.F_REG_PW) or "")
            st.progress(min(score, 4) / 4)

        confirm_password = st.text_input("Confirm Password", type="password", key=K.F_REG_CONFIRM)
        submit = st.form_submit_button("Register")

    if not submit:
        return

    # CSRF
    if not _csrf_check(K.CSRF_REG, SS.get(K.F_REG_CSRF, "")):
        st.error("Security token invalid. Please try again.")
        return

    # validações
    if not all([SS.get(K.F_REG_USER), SS.get(K.F_REG_EMAIL), SS.get(K.F_REG_PW), SS.get(K.F_REG_CONFIRM)]):
        st.error("Please fill in all fields.")
        return

    if not _USERNAME_RE.match(SS[K.F_REG_USER]):
        st.error("Username must be 3–32 chars and use only letters, numbers, dot, underscore, or dash.")
        return

    norm_email = (SS[K.F_REG_EMAIL] or "").strip().lower()
    if not _EMAIL_RE.match(norm_email):
        st.error("Please provide a valid email.")
        return

    ok, reason, _ = _password_ok(SS[K.F_REG_PW])
    if not ok:
        st.error(reason)
        return

    if SS[K.F_REG_PW] != SS[K.F_REG_CONFIRM]:
        st.error("Passwords do not match.")
        return

    # registro
    try:
        result = auth_manager.register_user(
            SS[K.F_REG_USER].strip(),
            norm_email,
            SS[K.F_REG_PW],
            UserRole.USER,
        )
    except Exception as e:
        st.error(_safe_msg("Registration service unavailable", e))
        return

    if getattr(result, "success", False):
        st.success("Registration successful! Please log in.")
        st.balloons()
        _clear_register_fields()
        SS[K.ACTIVE_TAB] = "Login"
        st.rerun()
    else:
        st.error(getattr(result, "message", "Registration failed. Please try again."))
        SS[K.ACTIVE_TAB] = "Register"
