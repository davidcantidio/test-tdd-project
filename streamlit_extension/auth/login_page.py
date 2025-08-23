"""Login and registration page for authentication."""

from __future__ import annotations

import os
import re
import time
import streamlit as st
from .auth_manager import AuthManager
from .user_model import UserRole


# ----------------------------- Config/Flags ----------------------------- #
AUTH_DEBUG = os.environ.get("AUTH_DEBUG", "").lower() in {"1", "true", "yes"}

# ----------------------------- Helpers ----------------------------- #

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.-]{3,32}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def _password_ok(pw: str) -> tuple[bool, str, int]:
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
    return True, "", score

def _init_session_defaults() -> None:
    st.session_state.setdefault("session_id", None)
    st.session_state.setdefault("current_user", None)
    st.session_state.setdefault("login_attempts", 0)
    st.session_state.setdefault("last_login_try_ts", 0.0)
    st.session_state.setdefault("auth_active_tab", "Login")  # "Login" | "Register"

def _ratelimit_login(max_attempts: int = 5, cooldown_sec: int = 30) -> tuple[bool, str]:
    """Limita tentativas na sessão atual (básico, não substitui rate limit global)."""
    attempts = int(st.session_state.get("login_attempts", 0))
    last_ts = float(st.session_state.get("last_login_try_ts", 0.0))
    now = time.time()
    if attempts >= max_attempts and (now - last_ts) < cooldown_sec:
        remaining = int(cooldown_sec - (now - last_ts))
        return False, f"Too many attempts. Please wait {remaining}s and try again."
    return True, ""

def _register_attempt(failed: bool) -> None:
    st.session_state["last_login_try_ts"] = time.time()
    if failed:
        st.session_state["login_attempts"] = int(st.session_state.get("login_attempts", 0)) + 1
    else:
        st.session_state["login_attempts"] = 0  # reset on success

def _safe_msg(prefix: str, exc: Exception) -> str:
    return f"{prefix}: {exc}" if AUTH_DEBUG else prefix

# ------------------------------ UI -------------------------------- #

def render_login_page():
    """Render login/registration page."""
    _init_session_defaults()
    st.title("🔐 Authentication")

    # já autenticado
    if st.session_state.get("current_user"):
        user = st.session_state["current_user"]
        st.success(f"You're logged in as **{getattr(user, 'username', 'user')}**.")
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("Log out"):
                st.session_state["session_id"] = None
                st.session_state["current_user"] = None
                st.toast("Logged out.")
                st.rerun()
        return

    auth_manager = AuthManager()

    # TDAH-friendly navigation with visual synchronization
    st.markdown("### 🚀 Quick Access")
    active = st.selectbox(
        "Choose action:",
        ["Login", "Register"],
        index=0 if st.session_state.get("auth_active_tab", "Login") == "Login" else 1,
        key="auth_mode_selector",
        help="Switch between login and registration"
    )
    
    # Update session state to match selection
    st.session_state["auth_active_tab"] = active
    
    # Always show the selected form (no conditional rendering)
    if active == "Login":
        render_login_form(auth_manager)
    else:
        render_registration_form(auth_manager)


def render_login_form(auth_manager: AuthManager):
    """Render login form."""
    st.subheader("Login")

    allowed, msg = _ratelimit_login()
    if not allowed:
        st.error(msg)
        return

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username", key="login_username")
        pw_col1, pw_col2 = st.columns([4, 1])
        with pw_col1:
            show_pw = st.checkbox("Show password", key="login_show_pw", value=False)
        with pw_col2:
            st.empty()
        password = st.text_input("Password", type="default" if show_pw else "password", key="login_password")

        col_a, col_b = st.columns([1, 1])
        with col_a:
            remember = st.checkbox("Remember this device", key="login_remember", value=False)
        with col_b:
            if st.link_button("Forgot password?", "#", help="Request password reset"):
                try:
                    # usa método se existir; se não, apenas informa
                    if hasattr(auth_manager, "send_password_reset"):
                        auth_manager.send_password_reset(username or "")
                        st.info("If this account exists, a reset message was sent.")
                    else:
                        st.info("Please contact support to reset your password.")
                except Exception as e:
                    st.error(_safe_msg("Password reset unavailable", e))

        submit = st.form_submit_button("Login", type="primary")

    if not submit:
        return

    if not username or not password:
        st.error("Please enter both username and password.")
        _register_attempt(failed=True)
        return

    # normalização leve
    norm_username = username.strip()
    try:
        result = auth_manager.authenticate(norm_username, password)
    except Exception as e:
        st.error(_safe_msg("Authentication service unavailable", e))
        _register_attempt(failed=True)
        return

    if getattr(result, "success", False):
        st.session_state["session_id"] = result.session_id
        st.session_state["current_user"] = result.user
        st.session_state["session_start_time"] = time.time()  # TDAH-friendly session tracking
        _register_attempt(failed=False)

        # sessão persistente se o gerenciador oferecer suporte
        if remember and hasattr(auth_manager, "issue_persistent_session"):
            try:
                auth_manager.issue_persistent_session(result.user)  # opcional
            except Exception as e:
                if AUTH_DEBUG:
                    st.warning(f"Persistent session not issued: {e}")

        st.success(f"Welcome back, {result.user.username}!")
        st.info("💡 **Your session will last 2 hours** with gentle reminders before expiring.")
        # limpa campos sensíveis
        for k in ("login_password", "login_show_pw"):
            st.session_state.pop(k, None)
        st.rerun()
    else:
        st.error(getattr(result, "message", "Invalid credentials."))
        _register_attempt(failed=True)


def render_registration_form(auth_manager: AuthManager):
    """Render registration form."""
    st.subheader("Register New Account")

    with st.form("register_form", clear_on_submit=False):
        username = st.text_input("Username", key="reg_username", help="3–32 chars: letters, numbers, . _ -")
        email = st.text_input("Email", key="reg_email")
        pw_col1, pw_col2 = st.columns([3, 2])
        with pw_col1:
            password = st.text_input("Password", type="password", key="reg_password")
        with pw_col2:
            # indicador simples de força
            ok_tmp, _, score = _password_ok(password or "")
            st.progress(min(score, 4) / 4)

        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
        submit = st.form_submit_button("Register")

    if not submit:
        return

    # validações
    if not all([username, email, password, confirm_password]):
        st.error("Please fill in all fields.")
        return

    if not _USERNAME_RE.match(username):
        st.error("Username must be 3–32 chars and use only letters, numbers, dot, underscore, or dash.")
        return

    norm_email = email.strip().lower()
    if not _EMAIL_RE.match(norm_email):
        st.error("Please provide a valid email.")
        return

    ok, reason, _ = _password_ok(password)
    if not ok:
        st.error(reason)
        return

    if password != confirm_password:
        st.error("Passwords do not match.")
        return

    # registro
    try:
        result = auth_manager.register_user(username.strip(), norm_email, password, UserRole.USER)
    except Exception as e:
        st.error(_safe_msg("Registration service unavailable", e))
        return

    if getattr(result, "success", False):
        st.success("Registration successful! Please log in.")
        st.balloons()
        # limpa campos
        for k in ("reg_username", "reg_email", "reg_password", "reg_confirm"):
            st.session_state.pop(k, None)
        # alterna para aba de Login
        st.session_state["auth_active_tab"] = "Login"
        st.rerun()
    else:
        st.error(getattr(result, "message", "Registration failed. Please try again."))
        st.session_state["auth_active_tab"] = "Register"
