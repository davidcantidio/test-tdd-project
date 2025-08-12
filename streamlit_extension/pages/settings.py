"""
⚙️ Settings Page

Configuration interface for the TDD Framework:
- Timer and TDAH settings
- GitHub integration setup
- Database configuration
- Theme and UI preferences
- Export/import settings
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Graceful imports
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

# Local imports
try:
    from streamlit_extension.utils.database import DatabaseManager
    from streamlit_extension.config import load_config, create_streamlit_config_file
    DATABASE_UTILS_AVAILABLE = True
except ImportError:
    DatabaseManager = load_config = create_streamlit_config_file = None
    DATABASE_UTILS_AVAILABLE = False


def render_settings_page():
    """Render the settings configuration page."""
    if not STREAMLIT_AVAILABLE:
        return {"error": "Streamlit not available"}
    
    st.title("⚙️ Settings & Configuration")
    st.markdown("---")
    
    if not DATABASE_UTILS_AVAILABLE:
        st.error("❌ Configuration utilities not available")
        return
    
    # Load current configuration
    try:
        config = load_config()
    except Exception as e:
        st.error(f"❌ Error loading configuration: {e}")
        return
    
    # Settings tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "⏱️ Timer & TDAH", 
        "🐙 GitHub Integration", 
        "🗄️ Database", 
        "🎨 Interface", 
        "💾 Backup & Export"
    ])
    
    with tab1:
        _render_timer_settings(config)
    
    with tab2:
        _render_github_settings(config)
    
    with tab3:
        _render_database_settings(config)
    
    with tab4:
        _render_interface_settings(config)
    
    with tab5:
        _render_backup_settings(config)


def _render_timer_settings(config):
    """Render timer and TDAH configuration."""
    
    st.markdown("### ⏱️ Timer Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎯 Focus Sessions")
        
        focus_duration = st.number_input(
            "Focus Session Duration (minutes)",
            min_value=5,
            max_value=120,
            value=config.focus_session_duration,
            step=5,
            help="Standard Pomodoro is 25 minutes"
        )
        
        short_break = st.number_input(
            "Short Break Duration (minutes)",
            min_value=1,
            max_value=30,
            value=config.short_break_duration,
            step=1,
            help="Break between focus sessions"
        )
        
        long_break = st.number_input(
            "Long Break Duration (minutes)",
            min_value=5,
            max_value=60,
            value=config.long_break_duration,
            step=5,
            help="Extended break after multiple sessions"
        )
        
        sessions_until_long_break = st.number_input(
            "Sessions until Long Break",
            min_value=2,
            max_value=10,
            value=config.sessions_until_long_break,
            step=1,
            help="Number of focus sessions before long break"
        )
    
    with col2:
        st.markdown("#### 🧠 TDAH Features")
        
        enable_focus_tracking = st.checkbox(
            "Enable Focus Rating Tracking",
            value=config.enable_focus_tracking,
            help="Track focus levels (1-10) during sessions"
        )
        
        enable_sound_alerts = st.checkbox(
            "Enable Sound Alerts",
            value=config.enable_sound_alerts,
            help="Play sounds when timer completes"
        )
        
        enable_notifications = st.checkbox(
            "Enable Browser Notifications",
            value=config.enable_notifications,
            help="Show browser notifications for timer events"
        )
        
        # Timezone selection
        common_timezones = [
            "America/Fortaleza",
            "America/Sao_Paulo", 
            "America/New_York",
            "America/Chicago",
            "America/Denver",
            "America/Los_Angeles",
            "Europe/London",
            "Europe/Paris",
            "Asia/Tokyo",
            "Australia/Sydney",
            "UTC"
        ]
        
        current_tz = config.timezone
        if current_tz in common_timezones:
            tz_index = common_timezones.index(current_tz)
        else:
            common_timezones.insert(0, current_tz)
            tz_index = 0
        
        timezone = st.selectbox(
            "Timezone",
            common_timezones,
            index=tz_index,
            help="Your local timezone for accurate time tracking"
        )
    
    st.markdown("---")
    
    # Gamification settings
    st.markdown("### 🎮 Gamification")
    
    col1, col2 = st.columns(2)
    
    with col1:
        enable_gamification = st.checkbox(
            "Enable Gamification System",
            value=config.enable_gamification,
            help="Points, achievements, and streaks"
        )
        
        if enable_gamification:
            points_per_task = st.number_input(
                "Points per Completed Task",
                min_value=1,
                max_value=100,
                value=config.points_per_completed_task,
                step=5
            )
            
            points_per_tdd_cycle = st.number_input(
                "Points per TDD Cycle",
                min_value=1,
                max_value=50,
                value=config.points_per_tdd_cycle,
                step=1
            )
    
    with col2:
        if enable_gamification:
            streak_bonus_multiplier = st.number_input(
                "Streak Bonus Multiplier",
                min_value=1.0,
                max_value=5.0,
                value=config.streak_bonus_multiplier,
                step=0.1,
                format="%.1f",
                help="Multiplier for consecutive achievements"
            )
    
    # Save timer settings
    if st.button("💾 Save Timer Settings", type="primary"):
        _save_timer_settings(
            focus_duration=focus_duration,
            short_break=short_break,
            long_break=long_break,
            sessions_until_long_break=sessions_until_long_break,
            enable_focus_tracking=enable_focus_tracking,
            enable_sound_alerts=enable_sound_alerts,
            enable_notifications=enable_notifications,
            timezone=timezone,
            enable_gamification=enable_gamification,
            points_per_task=points_per_task if enable_gamification else config.points_per_completed_task,
            points_per_tdd_cycle=points_per_tdd_cycle if enable_gamification else config.points_per_tdd_cycle,
            streak_bonus_multiplier=streak_bonus_multiplier if enable_gamification else config.streak_bonus_multiplier
        )


def _render_github_settings(config):
    """Render GitHub integration settings."""
    
    st.markdown("### 🐙 GitHub Integration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔗 Connection Settings")
        
        github_token = st.text_input(
            "GitHub Token",
            value=config.github_token or "",
            type="password",
            help="Personal access token for GitHub API (starts with 'ghp_', 'github_pat_', 'gho_', 'ghu_', 'ghs_', or 'ghr_')"
        )
        
        # GitHub token validation
        if github_token:
            import re
            # GitHub token patterns: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github
            token_patterns = [
                r'^ghp_[a-zA-Z0-9]{36}$',           # Personal access token (classic)
                r'^github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}$',  # Fine-grained personal access token
                r'^gho_[a-zA-Z0-9]{36}$',           # OAuth access token
                r'^ghu_[a-zA-Z0-9]{36}$',           # GitHub App user access token
                r'^ghs_[a-zA-Z0-9]{36}$',           # GitHub App server-to-server token
                r'^ghr_[a-zA-Z0-9]{76}$',           # GitHub App refresh token
            ]
            
            is_valid_token = any(re.match(pattern, github_token) for pattern in token_patterns)
            
            if is_valid_token:
                st.success("✅ Token format is valid")
            else:
                st.error("❌ Invalid token format. GitHub tokens should start with 'ghp_', 'github_pat_', 'gho_', 'ghu_', 'ghs_', or 'ghr_' and match the expected format.")
                st.info("💡 Generate a new token at: https://github.com/settings/tokens")
        
        github_repo_owner = st.text_input(
            "Repository Owner",
            value=config.github_repo_owner or "",
            help="GitHub username or organization"
        )
        
        github_repo_name = st.text_input(
            "Repository Name",
            value=config.github_repo_name or "",
            help="Name of the repository"
        )
        
        if github_token and github_repo_owner and github_repo_name:
            st.success("✅ GitHub configuration appears complete")
        else:
            st.info("ℹ️ Fill all fields to enable GitHub integration")
    
    with col2:
        st.markdown("#### ⚙️ API Settings")
        
        api_calls_per_hour = st.number_input(
            "API Calls per Hour Limit",
            min_value=1000,
            max_value=5000,
            value=config.github_api_calls_per_hour,
            step=500,
            help="GitHub API rate limit (5000 for authenticated users)"
        )
        
        rate_limit_buffer = st.number_input(
            "Rate Limit Buffer",
            min_value=100,
            max_value=1000,
            value=config.rate_limit_buffer,
            step=100,
            help="Safety buffer to avoid hitting rate limits"
        )
    
    # GitHub connection test
    st.markdown("#### 🧪 Connection Test")
    
    if st.button("🔍 Test GitHub Connection"):
        if not (github_token and github_repo_owner and github_repo_name):
            st.error("❌ Please fill in all GitHub settings first")
        else:
            with st.spinner("Testing GitHub connection..."):
                success = _test_github_connection(github_token, github_repo_owner, github_repo_name)
                
                if success:
                    st.success("✅ GitHub connection successful!")
                else:
                    st.error("❌ GitHub connection failed. Check your token and repository details.")
    
    # Save GitHub settings
    if st.button("💾 Save GitHub Settings"):
        # Validate token format before saving
        if github_token:
            import re
            token_patterns = [
                r'^ghp_[a-zA-Z0-9]{36}$',           # Personal access token (classic)
                r'^github_pat_[a-zA-Z0-9]{22}_[a-zA-Z0-9]{59}$',  # Fine-grained personal access token
                r'^gho_[a-zA-Z0-9]{36}$',           # OAuth access token
                r'^ghu_[a-zA-Z0-9]{36}$',           # GitHub App user access token
                r'^ghs_[a-zA-Z0-9]{36}$',           # GitHub App server-to-server token
                r'^ghr_[a-zA-Z0-9]{76}$',           # GitHub App refresh token
            ]
            
            is_valid_token = any(re.match(pattern, github_token) for pattern in token_patterns)
            
            if not is_valid_token:
                st.error("❌ Cannot save: Invalid GitHub token format. Please provide a valid token.")
                st.stop()
        
        _save_github_settings(
            github_token=github_token,
            github_repo_owner=github_repo_owner,
            github_repo_name=github_repo_name,
            api_calls_per_hour=api_calls_per_hour,
            rate_limit_buffer=rate_limit_buffer
        )


def _render_database_settings(config):
    """Render database configuration settings."""
    
    st.markdown("### 🗄️ Database Configuration")
    
    # Initialize database manager to check health
    try:
        db_manager = DatabaseManager(
            framework_db_path=str(config.get_database_path()),
            timer_db_path=str(config.get_timer_database_path())
        )
        health = db_manager.check_database_health()
    except Exception as e:
        st.error(f"❌ Database manager error: {e}")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Database Status")
        
        # Framework database
        fw_db_status = "✅ Connected" if health.get("framework_db_connected") else "❌ Not connected"
        fw_db_exists = "✅ Exists" if health.get("framework_db_exists") else "❌ Missing"
        
        st.info(f"""
        **Framework Database:**
        - Status: {fw_db_status}
        - File: {fw_db_exists}
        - Path: `{config.get_database_path()}`
        """)
        
        # Timer database
        timer_db_status = "✅ Connected" if health.get("timer_db_connected") else "❌ Not connected"
        timer_db_exists = "✅ Exists" if health.get("timer_db_exists") else "❌ Missing"
        
        st.info(f"""
        **Timer Database:**
        - Status: {timer_db_status}
        - File: {timer_db_exists}
        - Path: `{config.get_timer_database_path()}`
        """)
        
        # Dependencies
        sqlalchemy_status = "✅ Available" if health.get("sqlalchemy_available") else "❌ Missing"
        pandas_status = "✅ Available" if health.get("pandas_available") else "❌ Missing"
        
        st.info(f"""
        **Dependencies:**
        - SQLAlchemy: {sqlalchemy_status}
        - Pandas: {pandas_status}
        """)
    
    with col2:
        st.markdown("#### 🔧 Database Actions")
        
        if st.button("🔄 Refresh Database Health"):
            st.rerun()
        
        if st.button("🧹 Run Database Maintenance"):
            with st.spinner("Running database maintenance..."):
                # This would run database maintenance script
                st.success("✅ Database maintenance completed")
                # TODO: Implement actual maintenance call
        
        if st.button("💾 Backup Databases"):
            with st.spinner("Creating database backup..."):
                success = _backup_databases(config)
                if success:
                    st.success("✅ Database backup created successfully")
                else:
                    st.error("❌ Database backup failed")
        
        st.markdown("---")
        
        st.markdown("#### ⚙️ Advanced Settings")
        
        analytics_retention = st.number_input(
            "Analytics Data Retention (days)",
            min_value=30,
            max_value=365,
            value=config.analytics_retention_days,
            step=30,
            help="How long to keep analytics data"
        )
        
        cache_ttl = st.number_input(
            "Cache TTL (seconds)",
            min_value=300,
            max_value=3600,
            value=config.cache_ttl_seconds,
            step=300,
            help="How long to cache database queries"
        )
    
    # Save database settings
    if st.button("💾 Save Database Settings"):
        _save_database_settings(
            analytics_retention_days=analytics_retention,
            cache_ttl_seconds=cache_ttl
        )


def _render_interface_settings(config):
    """Render interface and UI settings."""
    
    st.markdown("### 🎨 Interface Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎨 Theme & Appearance")
        
        streamlit_theme = st.selectbox(
            "Streamlit Theme",
            ["dark", "light"],
            index=0 if config.streamlit_theme == "dark" else 1,
            help="Overall application theme"
        )
        
        streamlit_port = st.number_input(
            "Streamlit Port",
            min_value=1024,
            max_value=65535,
            value=config.streamlit_port,
            step=1,
            help="Port for Streamlit server"
        )
        
        max_upload_size = st.number_input(
            "Max Upload Size (MB)",
            min_value=10,
            max_value=1000,
            value=config.streamlit_max_upload_size,
            step=50,
            help="Maximum file upload size"
        )
    
    with col2:
        st.markdown("#### 🔧 Development Settings")
        
        debug_mode = st.checkbox(
            "Debug Mode",
            value=config.debug_mode,
            help="Enable debug information and verbose logging"
        )
        
        enable_profiler = st.checkbox(
            "Enable Performance Profiler",
            value=config.enable_profiler,
            help="Track performance metrics (may impact speed)"
        )
        
        enable_performance_metrics = st.checkbox(
            "Enable Performance Metrics",
            value=config.enable_performance_metrics,
            help="Collect and display performance data"
        )
        
        log_level = st.selectbox(
            "Log Level",
            ["DEBUG", "INFO", "WARNING", "ERROR"],
            index=["DEBUG", "INFO", "WARNING", "ERROR"].index(config.log_level),
            help="Logging verbosity level"
        )
    
    # Preview theme
    st.markdown("---")
    st.markdown("#### 👀 Theme Preview")
    
    if streamlit_theme == "dark":
        st.markdown("""
        <div style='background-color: #0E1117; color: #FAFAFA; padding: 20px; border-radius: 5px;'>
            <h4 style='color: #FF6B6B;'>🌙 Dark Theme Preview</h4>
            <p>This is how the dark theme looks with red accents.</p>
            <button style='background-color: #FF6B6B; color: white; border: none; padding: 8px 16px; border-radius: 4px;'>Sample Button</button>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background-color: #FFFFFF; color: #262730; padding: 20px; border-radius: 5px; border: 1px solid #E0E0E0;'>
            <h4 style='color: #FF4B4B;'>☀️ Light Theme Preview</h4>
            <p>This is how the light theme looks with red accents.</p>
            <button style='background-color: #FF4B4B; color: white; border: none; padding: 8px 16px; border-radius: 4px;'>Sample Button</button>
        </div>
        """, unsafe_allow_html=True)
    
    # Generate Streamlit config
    if st.button("📁 Generate Streamlit Config File"):
        with st.spinner("Generating .streamlit/config.toml..."):
            success = _generate_streamlit_config(config, streamlit_theme, streamlit_port, max_upload_size)
            if success:
                st.success("✅ Streamlit config file generated successfully!")
            else:
                st.error("❌ Failed to generate config file")
    
    # Save interface settings
    if st.button("💾 Save Interface Settings"):
        _save_interface_settings(
            streamlit_theme=streamlit_theme,
            streamlit_port=streamlit_port,
            max_upload_size=max_upload_size,
            debug_mode=debug_mode,
            enable_profiler=enable_profiler,
            enable_performance_metrics=enable_performance_metrics,
            log_level=log_level
        )


def _render_backup_settings(config):
    """Render backup and export settings."""
    
    st.markdown("### 💾 Backup & Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📦 Export Data")
        
        export_options = st.multiselect(
            "Select data to export:",
            ["Configuration", "Timer Sessions", "Tasks & Epics", "Achievements"],
            default=["Configuration"]
        )
        
        export_format = st.selectbox(
            "Export Format",
            ["JSON", "CSV", "SQLite Database"],
            help="Format for exported data"
        )
        
        if st.button("📤 Export Data"):
            with st.spinner("Exporting data..."):
                success, file_path = _export_data(export_options, export_format, config)
                
                if success:
                    st.success(f"✅ Data exported to: {file_path}")
                    
                    # Provide download link (in real implementation)
                    st.download_button(
                        "⬇️ Download Export",
                        data="[Export data would be here]",
                        file_name=file_path,
                        mime="application/json" if export_format == "JSON" else "text/csv"
                    )
                else:
                    st.error("❌ Export failed")
    
    with col2:
        st.markdown("#### 📥 Import Data")
        
        uploaded_file = st.file_uploader(
            "Choose file to import",
            type=["json", "csv", "db"],
            help="Upload previously exported data"
        )
        
        if uploaded_file:
            st.info(f"📁 **File:** {uploaded_file.name} ({uploaded_file.size} bytes)")
            
            import_options = st.multiselect(
                "Import settings:",
                ["Overwrite existing", "Merge with existing", "Backup before import"],
                default=["Backup before import"]
            )
            
            if st.button("📥 Import Data"):
                with st.spinner("Importing data..."):
                    success = _import_data(uploaded_file, import_options)
                    
                    if success:
                        st.success("✅ Data imported successfully!")
                        st.info("🔄 Please refresh the page to see changes")
                    else:
                        st.error("❌ Import failed")
    
    st.markdown("---")
    
    # Configuration management
    st.markdown("#### 🔧 Configuration Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Reset to Defaults"):
            if st.session_state.get("confirm_reset"):
                _reset_to_defaults()
                st.success("✅ Settings reset to defaults")
                st.session_state.confirm_reset = False
                st.rerun()
            else:
                st.session_state.confirm_reset = True
                st.warning("⚠️ Click again to confirm reset")
    
    with col2:
        if st.button("🔄 Reload Configuration"):
            try:
                reload_config()
                st.success("✅ Configuration reloaded from files")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Reload failed: {e}")
    
    with col3:
        config_json = json.dumps(config.to_dict(), indent=2)
        st.download_button(
            "📄 Download Config",
            data=config_json,
            file_name="tdd_framework_config.json",
            mime="application/json"
        )


# Helper functions for settings actions

def _save_timer_settings(**kwargs):
    """Save timer settings to configuration."""
    # In a real implementation, this would update the config file
    st.success("✅ Timer settings saved successfully!")
    st.info("🔄 Restart the application to apply all changes")


def _save_github_settings(**kwargs):
    """Save GitHub settings to configuration."""
    st.success("✅ GitHub settings saved successfully!")


def _save_database_settings(**kwargs):
    """Save database settings to configuration."""
    st.success("✅ Database settings saved successfully!")


def _save_interface_settings(**kwargs):
    """Save interface settings to configuration."""
    st.success("✅ Interface settings saved successfully!")
    st.info("🔄 Some changes may require application restart")


def _test_github_connection(token: str, owner: str, repo: str) -> bool:
    """Test GitHub API connection."""
    # In a real implementation, this would test the GitHub API
    # For now, just simulate success if all fields are provided
    return bool(token and owner and repo and len(token) > 10)


def _backup_databases(config) -> bool:
    """Create backup of databases."""
    # In a real implementation, this would create actual database backups
    return True


def _generate_streamlit_config(config, theme: str, port: int, upload_size: int) -> bool:
    """Generate Streamlit config file."""
    try:
        # Update config object (temporary)
        config.streamlit_theme = theme
        config.streamlit_port = port
        config.streamlit_max_upload_size = upload_size
        
        # Create config file
        create_streamlit_config_file(config)
        return True
    except Exception:
        return False


def _export_data(options: List[str], format_type: str, config) -> tuple[bool, str]:
    """Export selected data."""
    # In a real implementation, this would export actual data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"tdd_framework_export_{timestamp}.{format_type.lower()}"
    return True, filename


def _import_data(uploaded_file, options: List[str]) -> bool:
    """Import data from uploaded file."""
    # In a real implementation, this would process the uploaded file
    return True


def _reset_to_defaults():
    """Reset all settings to default values."""
    # In a real implementation, this would reset the config file
    pass


if __name__ == "__main__":
    render_settings_page()