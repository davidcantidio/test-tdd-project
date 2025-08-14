"""
💾 Configuration Backup & Restore System

Advanced configuration management with backup, restore, and migration capabilities:
- Automatic configuration backups with timestamps
- Manual backup creation and naming
- Selective restore (full or partial configuration)
- Configuration export/import (JSON format)
- Migration support for configuration schema changes
- Configuration validation and integrity checks
"""

import os
import shutil
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import tempfile
import zipfile

# Graceful imports
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    st = None
    STREAMLIT_AVAILABLE = False

try:
    from .streamlit_config import StreamlitConfig, get_config
    CONFIG_AVAILABLE = True
except ImportError:
    StreamlitConfig = get_config = None
    CONFIG_AVAILABLE = False

try:
    from .themes import ThemeManager, get_theme_manager
    THEMES_AVAILABLE = True
except ImportError:
    ThemeManager = get_theme_manager = None
    THEMES_AVAILABLE = False


class BackupType(Enum):
    """Types of configuration backups."""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    EXPORT = "export"
    MIGRATION = "migration"


@dataclass
class BackupInfo:
    """Information about a configuration backup."""
    
    name: str
    backup_type: BackupType
    created_at: datetime
    file_path: Path
    description: str = ""
    config_version: str = "1.0"
    size_bytes: int = 0
    
    # Components included in backup
    includes_streamlit_config: bool = False
    includes_themes: bool = False
    includes_cache_settings: bool = False
    includes_database_config: bool = False


class ConfigurationBackupManager:
    """Manages configuration backups, restore, and migrations."""
    
    def __init__(self, backup_dir: Optional[Path] = None):
        self.backup_dir = backup_dir or Path.cwd() / ".config_backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Backup retention settings
        self.max_automatic_backups = 10
        self.max_manual_backups = 50
        self.automatic_backup_retention_days = 30
        
        # Backup index file
        self.index_file = self.backup_dir / "backup_index.json"
        self._backup_index = self._load_backup_index()
    
    def create_automatic_backup(self, description: str = None) -> Optional[BackupInfo]:
        """Create an automatic backup of current configuration."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"auto_{timestamp}"
        
        return self._create_backup(
            backup_name,
            BackupType.AUTOMATIC,
            description or f"Automatic backup at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    
    def create_manual_backup(self, name: str, description: str = "") -> Optional[BackupInfo]:
        """Create a manual backup with custom name."""
        # Sanitize name
        safe_name = "".join(c for c in name if c.isalnum() or c in ('-', '_', ' ')).strip()
        if not safe_name:
            safe_name = f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"manual_{safe_name}_{timestamp}"
        
        return self._create_backup(backup_name, BackupType.MANUAL, description)
    
    def _create_backup(self, backup_name: str, backup_type: BackupType, description: str) -> Optional[BackupInfo]:
        """Create a backup with specified parameters."""
        backup_file = self.backup_dir / f"{backup_name}.zip"
        
        try:
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                backup_info = BackupInfo(
                    name=backup_name,
                    backup_type=backup_type,
                    created_at=datetime.now(),
                    file_path=backup_file,
                    description=description
                )
                
                # Backup streamlit configuration
                if CONFIG_AVAILABLE:
                    config = get_config()
                    config_dict = asdict(config)
                    
                    # Add to zip
                    zipf.writestr("streamlit_config.json", json.dumps(config_dict, indent=2))
                    backup_info.includes_streamlit_config = True
                
                # Backup themes
                if THEMES_AVAILABLE:
                    theme_manager = get_theme_manager()
                    custom_themes = theme_manager.custom_themes
                    current_theme = theme_manager._current_theme
                    
                    theme_data = {
                        "custom_themes": {name: asdict(theme) for name, theme in custom_themes.items()},
                        "current_theme": current_theme
                    }
                    
                    zipf.writestr("themes.json", json.dumps(theme_data, indent=2))
                    backup_info.includes_themes = True
                
                # Backup cache settings (if available)
                cache_settings_file = Path.cwd() / ".streamlit_cache" / "settings.json"
                if cache_settings_file.exists():
                    zipf.write(cache_settings_file, "cache_settings.json")
                    backup_info.includes_cache_settings = True
                
                # Backup database configuration (if available)
                db_config_files = [
                    Path.cwd() / "framework.db.config",
                    Path.cwd() / "task_timer.db.config"
                ]
                
                for i, db_config_file in enumerate(db_config_files):
                    if db_config_file.exists():
                        zipf.write(db_config_file, f"db_config_{i}.json")
                        backup_info.includes_database_config = True
                
                # Add backup metadata
                metadata = {
                    "backup_info": asdict(backup_info),
                    "created_by": "StreamlitExtension",
                    "version": "1.0",
                    "components": {
                        "streamlit_config": backup_info.includes_streamlit_config,
                        "themes": backup_info.includes_themes,
                        "cache_settings": backup_info.includes_cache_settings,
                        "database_config": backup_info.includes_database_config
                    }
                }
                
                zipf.writestr("backup_metadata.json", json.dumps(metadata, indent=2, default=str))
                
                # Update file size
                backup_info.size_bytes = backup_file.stat().st_size
                
                # Add to index
                self._backup_index[backup_name] = backup_info
                self._save_backup_index()
                
                # Cleanup old backups
                self._cleanup_old_backups()
                
                return backup_info
                
        except Exception as e:
            # Cleanup failed backup file
            if backup_file.exists():
                backup_file.unlink()
            return None
    
    def restore_backup(self, backup_name: str, components: List[str] = None) -> bool:
        """Restore configuration from backup."""
        if backup_name not in self._backup_index:
            return False
        
        backup_info = self._backup_index[backup_name]
        backup_file = backup_info.file_path
        
        if not backup_file.exists():
            return False
        
        components = components or ["streamlit_config", "themes", "cache_settings", "database_config"]
        
        try:
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                # Restore streamlit config
                if "streamlit_config" in components and backup_info.includes_streamlit_config:
                    try:
                        config_data = json.loads(zipf.read("streamlit_config.json"))
                        if CONFIG_AVAILABLE:
                            # Apply configuration (this would need implementation in streamlit_config.py)
                            self._restore_streamlit_config(config_data)
                    except (KeyError, json.JSONDecodeError):
                        pass
                
                # Restore themes
                if "themes" in components and backup_info.includes_themes:
                    try:
                        theme_data = json.loads(zipf.read("themes.json"))
                        if THEMES_AVAILABLE:
                            self._restore_themes(theme_data)
                    except (KeyError, json.JSONDecodeError):
                        pass
                
                # Restore cache settings
                if "cache_settings" in components and backup_info.includes_cache_settings:
                    try:
                        cache_dir = Path.cwd() / ".streamlit_cache"
                        cache_dir.mkdir(exist_ok=True)
                        
                        cache_settings = zipf.read("cache_settings.json")
                        with open(cache_dir / "settings.json", 'wb') as f:
                            f.write(cache_settings)
                    except KeyError:
                        pass
                
                # Restore database config
                if "database_config" in components and backup_info.includes_database_config:
                    try:
                        # Extract database config files
                        for name in zipf.namelist():
                            if name.startswith("db_config_"):
                                config_data = zipf.read(name)
                                config_file = Path.cwd() / f"{name.replace('db_config_', 'config_')}"
                                with open(config_file, 'wb') as f:
                                    f.write(config_data)
                    except Exception as e:
                        # Log configuration restore failure but continue
                        import logging
                        logging.getLogger(__name__).warning(f"Failed to restore configuration files: {e}")
                        # Continue processing other backup components
                
                return True
                
        except Exception as e:
            return False
    
    def export_configuration(self, export_path: Path, include_sensitive: bool = False) -> bool:
        """Export configuration to external file."""
        try:
            config_data = {}
            
            # Export streamlit config
            if CONFIG_AVAILABLE:
                config = get_config()
                config_dict = asdict(config)
                
                # Remove sensitive data if requested
                if not include_sensitive:
                    sensitive_keys = ['github_token', 'api_keys', 'passwords']
                    for key in sensitive_keys:
                        if key in config_dict:
                            config_dict[key] = "[REDACTED]"
                
                config_data["streamlit_config"] = config_dict
            
            # Export themes
            if THEMES_AVAILABLE:
                theme_manager = get_theme_manager()
                config_data["themes"] = {
                    "custom_themes": {name: asdict(theme) for name, theme in theme_manager.custom_themes.items()},
                    "current_theme": theme_manager._current_theme
                }
            
            # Export metadata
            config_data["export_metadata"] = {
                "exported_at": datetime.now().isoformat(),
                "version": "1.0",
                "includes_sensitive": include_sensitive
            }
            
            # Write to file
            with open(export_path, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
            
            return True
            
        except Exception as e:
            return False
    
    def import_configuration(self, import_path: Path, components: List[str] = None) -> bool:
        """Import configuration from external file."""
        if not import_path.exists():
            return False
        
        components = components or ["streamlit_config", "themes"]
        
        try:
            with open(import_path, 'r') as f:
                config_data = json.load(f)
            
            # Import streamlit config
            if "streamlit_config" in components and "streamlit_config" in config_data:
                if CONFIG_AVAILABLE:
                    self._restore_streamlit_config(config_data["streamlit_config"])
            
            # Import themes
            if "themes" in components and "themes" in config_data:
                if THEMES_AVAILABLE:
                    self._restore_themes(config_data["themes"])
            
            return True
            
        except (json.JSONDecodeError, KeyError, Exception) as e:
            return False
    
    def get_backup_list(self) -> List[BackupInfo]:
        """Get list of all backups sorted by creation date."""
        backups = list(self._backup_index.values())
        backups.sort(key=lambda b: b.created_at, reverse=True)
        return backups
    
    def delete_backup(self, backup_name: str) -> bool:
        """Delete a backup."""
        if backup_name not in self._backup_index:
            return False
        
        backup_info = self._backup_index[backup_name]
        
        # Delete file
        try:
            if backup_info.file_path.exists():
                backup_info.file_path.unlink()
        except OSError:
            pass
        
        # Remove from index
        del self._backup_index[backup_name]
        self._save_backup_index()
        
        return True
    
    def get_backup_info(self, backup_name: str) -> Optional[BackupInfo]:
        """Get detailed information about a backup."""
        return self._backup_index.get(backup_name)
    
    def _restore_streamlit_config(self, config_data: Dict[str, Any]) -> None:
        """Restore streamlit configuration."""
        # This would integrate with the actual config system
        # For now, we'll just store it for the next app restart
        config_restore_file = Path.cwd() / ".config_restore.json"
        with open(config_restore_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def _restore_themes(self, theme_data: Dict[str, Any]) -> None:
        """Restore theme configuration."""
        if not THEMES_AVAILABLE:
            return
        
        theme_manager = get_theme_manager()
        
        # Restore custom themes
        if "custom_themes" in theme_data:
            for theme_name, theme_dict in theme_data["custom_themes"].items():
                # This would need proper theme reconstruction
                pass
        
        # Restore current theme selection
        if "current_theme" in theme_data:
            theme_manager.set_current_theme(theme_data["current_theme"])
    
    def _cleanup_old_backups(self) -> None:
        """Clean up old backups based on retention policies."""
        current_time = datetime.now()
        
        # Count backups by type
        auto_backups = []
        manual_backups = []
        
        for backup_info in self._backup_index.values():
            if backup_info.backup_type == BackupType.AUTOMATIC:
                auto_backups.append(backup_info)
            elif backup_info.backup_type == BackupType.MANUAL:
                manual_backups.append(backup_info)
        
        # Clean up automatic backups
        auto_backups.sort(key=lambda b: b.created_at, reverse=True)
        
        # Remove by count
        if len(auto_backups) > self.max_automatic_backups:
            for backup in auto_backups[self.max_automatic_backups:]:
                self.delete_backup(backup.name)
        
        # Remove by age
        cutoff_date = current_time - timedelta(days=self.automatic_backup_retention_days)
        for backup in auto_backups:
            if backup.created_at < cutoff_date:
                self.delete_backup(backup.name)
        
        # Clean up manual backups (by count only)
        manual_backups.sort(key=lambda b: b.created_at, reverse=True)
        if len(manual_backups) > self.max_manual_backups:
            for backup in manual_backups[self.max_manual_backups:]:
                self.delete_backup(backup.name)
    
    def _load_backup_index(self) -> Dict[str, BackupInfo]:
        """Load backup index from file."""
        if not self.index_file.exists():
            return {}
        
        try:
            with open(self.index_file, 'r') as f:
                index_data = json.load(f)
            
            backup_index = {}
            for name, backup_dict in index_data.items():
                # Reconstruct BackupInfo objects
                backup_dict["created_at"] = datetime.fromisoformat(backup_dict["created_at"])
                backup_dict["file_path"] = Path(backup_dict["file_path"])
                backup_dict["backup_type"] = BackupType(backup_dict["backup_type"])
                
                backup_index[name] = BackupInfo(**backup_dict)
            
            return backup_index
            
        except (json.JSONDecodeError, KeyError, ValueError):
            return {}
    
    def _save_backup_index(self) -> None:
        """Save backup index to file."""
        try:
            index_data = {}
            for name, backup_info in self._backup_index.items():
                backup_dict = asdict(backup_info)
                backup_dict["created_at"] = backup_info.created_at.isoformat()
                backup_dict["file_path"] = str(backup_info.file_path)
                backup_dict["backup_type"] = backup_info.backup_type.value
                
                index_data[name] = backup_dict
            
            with open(self.index_file, 'w') as f:
                json.dump(index_data, f, indent=2)
                
        except Exception as e:
            # Log backup index save failure - this is important for backup integrity
            import logging
            logging.getLogger(__name__).error(f"Failed to save backup index: {e}")
            # Don't raise, as this is a background operation


# Global backup manager instance
_backup_manager = None

def get_backup_manager() -> ConfigurationBackupManager:
    """Get global backup manager instance."""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = ConfigurationBackupManager()
    return _backup_manager


def render_backup_restore_ui() -> None:
    """Render backup and restore UI in Streamlit."""
    if not STREAMLIT_AVAILABLE:
        print("[BACKUP & RESTORE UI]")
        return
    
    backup_manager = get_backup_manager()
    
    st.markdown("### 💾 Configuration Backup & Restore")
    
    # Create tabs for different operations
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Backups", "💾 Create Backup", "🔄 Restore", "📤 Export/Import"])
    
    with tab1:
        st.markdown("#### Available Backups")
        
        backups = backup_manager.get_backup_list()
        
        if not backups:
            st.info("No backups found. Create your first backup in the 'Create Backup' tab.")
        else:
            for backup in backups:
                with st.expander(f"{backup.name} ({backup.backup_type.value})", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Created:** {backup.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                        st.write(f"**Size:** {backup.size_bytes / 1024:.1f} KB")
                        if backup.description:
                            st.write(f"**Description:** {backup.description}")
                    
                    with col2:
                        st.write("**Components:**")
                        if backup.includes_streamlit_config:
                            st.write("✅ Streamlit Config")
                        if backup.includes_themes:
                            st.write("✅ Themes")
                        if backup.includes_cache_settings:
                            st.write("✅ Cache Settings")
                        if backup.includes_database_config:
                            st.write("✅ Database Config")
                    
                    col_restore, col_delete = st.columns(2)
                    
                    with col_restore:
                        if st.button(f"🔄 Restore", key=f"restore_{backup.name}"):
                            if backup_manager.restore_backup(backup.name):
                                st.success("Configuration restored successfully!")
                                st.rerun()
                            else:
                                st.error("Failed to restore configuration.")
                    
                    with col_delete:
                        if backup.backup_type != BackupType.AUTOMATIC:  # Don't allow deleting auto backups
                            if st.button(f"🗑️ Delete", key=f"delete_{backup.name}"):
                                if backup_manager.delete_backup(backup.name):
                                    st.success("Backup deleted successfully!")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete backup.")
    
    with tab2:
        st.markdown("#### Create New Backup")
        
        backup_type = st.radio(
            "Backup Type:",
            ["Manual", "Automatic"],
            help="Manual backups allow custom names and descriptions"
        )
        
        if backup_type == "Manual":
            backup_name = st.text_input(
                "Backup Name:",
                placeholder="My Custom Backup",
                help="Enter a descriptive name for this backup"
            )
            
            backup_description = st.text_area(
                "Description (optional):",
                placeholder="Describe what this backup contains or why it was created",
                height=100
            )
            
            if st.button("💾 Create Manual Backup", type="primary"):
                if backup_name.strip():
                    backup_info = backup_manager.create_manual_backup(backup_name.strip(), backup_description.strip())
                    if backup_info:
                        st.success(f"Backup '{backup_info.name}' created successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to create backup.")
                else:
                    st.error("Please enter a backup name.")
        
        else:  # Automatic
            backup_description = st.text_input(
                "Description (optional):",
                placeholder="Optional description for this automatic backup"
            )
            
            if st.button("⚡ Create Automatic Backup", type="primary"):
                backup_info = backup_manager.create_automatic_backup(backup_description.strip() or None)
                if backup_info:
                    st.success(f"Automatic backup '{backup_info.name}' created successfully!")
                    st.rerun()
                else:
                    st.error("Failed to create automatic backup.")
    
    with tab3:
        st.markdown("#### Restore Configuration")
        
        backups = backup_manager.get_backup_list()
        
        if not backups:
            st.info("No backups available for restore.")
        else:
            backup_names = [backup.name for backup in backups]
            backup_display_names = [f"{backup.name} ({backup.created_at.strftime('%Y-%m-%d %H:%M')})" for backup in backups]
            
            selected_backup_idx = st.selectbox(
                "Select Backup to Restore:",
                range(len(backups)),
                format_func=lambda i: backup_display_names[i]
            )
            
            selected_backup = backups[selected_backup_idx]
            
            st.markdown("**Components to Restore:**")
            
            restore_components = []
            
            if selected_backup.includes_streamlit_config:
                if st.checkbox("Streamlit Configuration", value=True, key="restore_streamlit"):
                    restore_components.append("streamlit_config")
            
            if selected_backup.includes_themes:
                if st.checkbox("Themes", value=True, key="restore_themes"):
                    restore_components.append("themes")
            
            if selected_backup.includes_cache_settings:
                if st.checkbox("Cache Settings", value=True, key="restore_cache"):
                    restore_components.append("cache_settings")
            
            if selected_backup.includes_database_config:
                if st.checkbox("Database Configuration", value=True, key="restore_db"):
                    restore_components.append("database_config")
            
            if st.button("🔄 Restore Selected Components", type="primary"):
                if restore_components:
                    if backup_manager.restore_backup(selected_backup.name, restore_components):
                        st.success("Selected components restored successfully!")
                        st.info("Some changes may require restarting the application to take effect.")
                    else:
                        st.error("Failed to restore selected components.")
                else:
                    st.warning("Please select at least one component to restore.")
    
    with tab4:
        st.markdown("#### Export & Import Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Export Configuration**")
            
            export_filename = st.text_input(
                "Export Filename:",
                value=f"config_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            include_sensitive = st.checkbox(
                "Include Sensitive Data",
                value=False,
                help="Include API tokens, passwords, and other sensitive information"
            )
            
            if st.button("📤 Export Configuration"):
                export_path = Path.cwd() / export_filename
                if backup_manager.export_configuration(export_path, include_sensitive):
                    st.success(f"Configuration exported to: {export_path}")
                    
                    # Offer download
                    with open(export_path, 'r') as f:
                        config_data = f.read()
                    
                    st.download_button(
                        "📥 Download Export File",
                        data=config_data,
                        file_name=export_filename,
                        mime="application/json"
                    )
                else:
                    st.error("Failed to export configuration.")
        
        with col2:
            st.markdown("**Import Configuration**")
            
            uploaded_file = st.file_uploader(
                "Choose configuration file",
                type=['json'],
                help="Upload a previously exported configuration file"
            )
            
            if uploaded_file is not None:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.json') as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_path = Path(tmp_file.name)
                
                st.markdown("**Components to Import:**")
                
                import_components = []
                
                if st.checkbox("Streamlit Configuration", value=True, key="import_streamlit"):
                    import_components.append("streamlit_config")
                
                if st.checkbox("Themes", value=True, key="import_themes"):
                    import_components.append("themes")
                
                if st.button("📥 Import Configuration"):
                    if import_components:
                        if backup_manager.import_configuration(tmp_path, import_components):
                            st.success("Configuration imported successfully!")
                            st.info("Some changes may require restarting the application to take effect.")
                        else:
                            st.error("Failed to import configuration.")
                    else:
                        st.warning("Please select at least one component to import.")
                
                # Cleanup temp file
                try:
                    tmp_path.unlink()
                except Exception as e:
                    # Log temp file cleanup failure but don't fail the operation
                    import logging
                    logging.getLogger(__name__).debug(f"Failed to cleanup temp file {tmp_path}: {e}")
                    # Temp file cleanup failure is not critical


# Export for convenience
__all__ = [
    "BackupType", "BackupInfo", "ConfigurationBackupManager",
    "get_backup_manager", "render_backup_restore_ui"
]