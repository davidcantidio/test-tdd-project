# 🔧 TDD Framework - Quick Troubleshooting

> Essential solutions for common issues

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 🚨 Common Issues

### **Setup & Dependencies**

**Missing modules:** `pip install streamlit plotly sqlite3 pandas pathlib`  
**Permission errors:** `sudo chown -R $USER:$USER .`  
**Git not initialized:** `git init && git add . && git commit -m "Initial commit"`

### **Database Issues**

**Database locked:** `rm -f *.db-wal *.db-shm` then restart  
**Schema errors:** `python scripts/maintenance/database_maintenance.py`  
**Connection pool:** Restart application, check for open connections

### **Streamlit Issues**

**Port conflicts:** `streamlit run streamlit_extension/streamlit_app.py --server.port 8502`  
**Import errors:** `export PYTHONPATH="${PYTHONPATH}:$(pwd)"`  
**Memory issues:** Clear browser cache, restart Streamlit

### **Authentication Issues**

**Login fails:** Check `TDD_ENVIRONMENT` variable, restart app  
**Session expired:** Clear browser cookies, log in again  
**Registration errors:** Ensure unique email, check database permissions

### **Security Errors**

**CSRF protection:** Refresh page to get new token  
**Rate limiting:** Wait 1 minute, then retry  
**XSS warnings:** Use plain text in form fields

## 🧪 Testing Issues

### **Test Failures**

**Import errors:** `export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"`  
**Database tests:** `python -m pytest tests/ -v --tb=short`  
**Hanging tests:** `timeout 30 python -m pytest tests/test_connection_pool.py`

### **Coverage Issues**

**Low coverage:** `pytest tests/ --cov --cov-report=html`  
**Missing files:** Check imports and file paths in test files

## 🏗️ Service Layer Issues

### **ServiceResult Errors**

**Wrong pattern:** Use `if result.success:` not `if result.is_success`  
**Import error:** `from streamlit_extension.services.base import ServiceResult`

### **Dependency Injection**

**Service not found:** Check `ServiceContainer` registration  
**Container fails:** Restart app, check service imports

## 🌍 Environment Issues

### **Configuration**

**Missing variables:** Set `TDD_ENVIRONMENT=development`  
**Secrets error:** Check Google OAuth credentials in env vars  
**YAML issues:** Validate YAML syntax in `config/environments/`

### **Health Monitoring**

**Health check fails:** `python streamlit_extension/endpoints/health.py`  
**Performance warnings:** Check database response times, restart if needed

## ⏰ Timer & Analytics

### **Timer Not Working**

**Database init:** `python tdah_tools/task_timer.py init`  
**Permissions:** `chmod 666 task_timer.db`  
**Session issues:** Clear session state, restart timer

### **Analytics Errors**

**No data:** Ensure tasks have TDD phases set  
**Calculation errors:** Check date formats and duration values  
**Chart issues:** Update Plotly version: `pip install --upgrade plotly`

## 🔄 Performance Issues

### **Slow Loading**

**Database:** Run `python scripts/maintenance/database_maintenance.py`  
**Cache:** Clear `.streamlit` cache directory  
**Memory:** Restart Streamlit application

### **High CPU/Memory**

**Reduce data:** Filter large datasets, use pagination  
**Optimize queries:** Check DatabaseManager query efficiency  
**Browser:** Close other tabs, clear browser cache

## 🐛 Debugging Commands

### **Quick Diagnostics**

```bash
# System check
python --version && streamlit --version

# Database status
python -c "from streamlit_extension.utils.database import DatabaseManager; print('DB OK:', DatabaseManager().health_check())"

# Authentication test
python -c "from streamlit_extension.auth.auth_manager import AuthManager; print('Auth OK:', AuthManager().health_check())"

# Service test
python -c "from streamlit_extension.services import ServiceContainer; print('Services OK:', ServiceContainer().health_check())"
```

### **Reset Commands**

```bash
# Soft reset (keeps data)
rm -rf .streamlit/
rm -f *.db-wal *.db-shm
streamlit cache clear

# Hard reset (loses session data)
rm -rf .streamlit/
git stash
git reset --hard HEAD
```

## 🆘 Emergency Solutions

### **Application Won't Start**

1. `pip install --upgrade streamlit plotly`
2. `export PYTHONPATH="${PYTHONPATH}:$(pwd)"`
3. `streamlit run streamlit_extension/streamlit_app.py`

### **Database Corruption**

1. `cp framework.db framework.db.backup`
2. `python scripts/maintenance/database_maintenance.py backup`
3. Restore from backup if needed

### **Authentication Broken**

1. Clear browser cookies/cache
2. Set `TDD_ENVIRONMENT=development`
3. Restart Streamlit application

## 📞 Getting Help

### **Collect Debug Info**

```bash
# Generate debug report
python --version > debug.txt
pip list | grep -E "(streamlit|plotly)" >> debug.txt
ls -la *.db >> debug.txt
git status >> debug.txt
```

### **Common Fix Sequence**

1. **Restart:** `Ctrl+C` then restart Streamlit
2. **Clear cache:** `streamlit cache clear`
3. **Reset environment:** `export PYTHONPATH="${PYTHONPATH}:$(pwd)"`
4. **Database check:** `python scripts/maintenance/database_maintenance.py health`
5. **Dependencies:** `pip install --upgrade streamlit plotly pandas`

### **Support Channels**

- **Issues:** Create GitHub issue with debug info
- **Quick help:** Check existing GitHub discussions
- **Enterprise:** Contact via documentation links

---

**💡 Pro Tips:**
- Always restart Streamlit after configuration changes
- Use `streamlit cache clear` for mysterious errors
- Check browser developer console for JavaScript errors
- Backup database before major operations

**🔧 Still stuck?** Include debug info when asking for help!