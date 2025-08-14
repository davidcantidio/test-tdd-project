# 🚨 Disaster Recovery Plan
## Duration System Framework - Enterprise Security Edition

**Document Version:** 1.0  
**Last Updated:** 2025-08-13  
**Classification:** CONFIDENTIAL  
**Owner:** Duration System Security Team  

---

## 📋 Executive Summary

This Disaster Recovery Plan (DRP) addresses RES-005 audit finding and provides comprehensive procedures for recovering the Duration System Framework from various disaster scenarios. The plan ensures business continuity, data protection, and rapid service restoration.

### Recovery Objectives
- **RTO (Recovery Time Objective):** 4 hours for critical services
- **RPO (Recovery Point Objective):** 1 hour maximum data loss
- **Service Level:** 99.9% availability target
- **Data Integrity:** Zero tolerance for data corruption

---

## 🏗️ System Architecture Overview

### Critical Components
1. **Primary Database** (`framework.db`) - Core application data
2. **Timer Database** (`task_timer.db`) - Time tracking data  
3. **GDPR Compliance Database** (`gdpr_compliance.db`) - Compliance records
4. **Cache System** (`.streamlit_cache/`) - Performance cache
5. **Epic JSON Files** (`epics/user_epics/`) - Structured project data
6. **Security Logs** (`gdpr_audit.log`, `security.log`) - Audit trails
7. **Application Code** - Source code and configurations

### Dependencies
- Python 3.12+ runtime environment
- SQLite/SQLCipher database engine
- Streamlit framework
- External libraries (see `pyproject.toml`)
- Network connectivity for remote operations

---

## 🎯 Disaster Scenarios & Response

### Scenario 1: Database Corruption
**Likelihood:** Medium | **Impact:** High | **RTO:** 2 hours | **RPO:** 30 minutes

#### Detection Signs
- SQLite database integrity check failures
- Application crashes on database access
- Data consistency errors in logs
- User reports of missing/corrupted data

#### Response Procedure
1. **Immediate Actions (0-15 minutes)**
   ```bash
   # Stop all services immediately
   pkill -f streamlit
   pkill -f python
   
   # Isolate corrupted databases
   mkdir -p /backup/corrupted/$(date +%Y%m%d_%H%M%S)
   cp framework.db /backup/corrupted/$(date +%Y%m%d_%H%M%S)/
   cp task_timer.db /backup/corrupted/$(date +%Y%m%d_%H%M%S)/
   cp gdpr_compliance.db /backup/corrupted/$(date +%Y%m%d_%H%M%S)/
   ```

2. **Assessment (15-30 minutes)**
   ```bash
   # Check database integrity
   sqlite3 framework.db "PRAGMA integrity_check;"
   sqlite3 task_timer.db "PRAGMA integrity_check;"
   sqlite3 gdpr_compliance.db "PRAGMA integrity_check;"
   
   # Analyze corruption extent
   python test_database_integrity.py --verbose
   ```

3. **Recovery (30-120 minutes)**
   ```bash
   # Restore from latest backup
   cp /backup/daily/$(ls -t /backup/daily/ | head -n1)/framework.db ./
   cp /backup/daily/$(ls -t /backup/daily/ | head -n1)/task_timer.db ./
   cp /backup/daily/$(ls -t /backup/daily/ | head -n1)/gdpr_compliance.db ./
   
   # Verify restored databases
   python test_database_integrity.py
   
   # Apply any recent changes from transaction logs
   python recovery_scripts/apply_transaction_logs.py
   
   # Restart services
   python -m streamlit run dashboard.py --server.port 8501
   ```

4. **Validation (15 minutes)**
   - Run full test suite: `pytest tests/ -v`
   - Verify user access and core functions
   - Check data consistency with pre-disaster snapshots
   - Update incident log and notify stakeholders

---

### Scenario 2: Complete System Failure
**Likelihood:** Low | **Impact:** Critical | **RTO:** 4 hours | **RPO:** 1 hour

#### Detection Signs
- Total system unresponsiveness
- Hardware failure indicators
- Network connectivity loss
- Multiple service failures

#### Response Procedure
1. **Emergency Assessment (0-30 minutes)**
   ```bash
   # Check system status from backup location
   ssh backup-server "systemctl status duration-system"
   
   # Verify backup integrity
   ssh backup-server "cd /backup && ./verify_backups.sh"
   
   # Assess damage scope
   ping primary-server
   nmap -sP primary-server-network
   ```

2. **Activate Backup Environment (30-180 minutes)**
   ```bash
   # On backup server
   cd /backup/emergency-restore
   
   # Deploy clean environment
   ./setup_emergency_environment.sh
   
   # Restore all databases
   cp latest-backup/framework.db /emergency/duration-system/
   cp latest-backup/task_timer.db /emergency/duration-system/
   cp latest-backup/gdpr_compliance.db /emergency/duration-system/
   
   # Restore application code
   rsync -av latest-backup/duration-system/ /emergency/duration-system/
   
   # Install dependencies
   cd /emergency/duration-system
   python -m pip install -e .
   ```

3. **Service Restoration (180-240 minutes)**
   ```bash
   # Start services with enhanced monitoring
   python -m streamlit run dashboard.py --server.port 8501 --server.enableCORS false
   
   # Enable security features
   python -c "from duration_system.gdpr_integration import init_gdpr_for_framework; init_gdpr_for_framework()"
   
   # Verify all systems
   ./disaster_recovery/full_system_check.sh
   ```

4. **User Communication**
   - Send emergency notification to all users
   - Update status page with estimated restoration time
   - Provide alternative access methods if available

---

### Scenario 3: Data Breach
**Likelihood:** Medium | **Impact:** Critical | **RTO:** 1 hour | **RPO:** Real-time

#### Detection Signs
- Unauthorized access alerts
- Unusual database query patterns
- Security log anomalies
- External breach notifications

#### Response Procedure
1. **Immediate Containment (0-15 minutes)**
   ```bash
   # Isolate affected systems
   sudo iptables -A INPUT -j DROP
   sudo iptables -A OUTPUT -j DROP
   
   # Stop all services
   pkill -f streamlit
   
   # Enable emergency logging
   python security/enable_emergency_logging.py
   
   # Preserve evidence
   cp -r . /forensics/incident-$(date +%Y%m%d_%H%M%S)/
   ```

2. **Assessment & Investigation (15-45 minutes)**
   ```bash
   # Analyze access logs
   python security/analyze_breach.py --incident-id $(date +%Y%m%d_%H%M%S)
   
   # Check data integrity
   python security/verify_data_integrity.py
   
   # Identify compromised accounts
   python security/identify_compromised_users.py
   ```

3. **Notification & Compliance (45-60 minutes)**
   ```bash
   # Generate GDPR breach report
   python duration_system/gdpr_compliance.py --generate-breach-report
   
   # Notify affected users (if required)
   python security/notify_breach_users.py --incident-id $(date +%Y%m%d_%H%M%S)
   
   # Prepare regulatory notifications
   python security/prepare_regulatory_notice.py
   ```

---

## 💾 Backup Strategy

### Automated Backup Schedule
```bash
# Daily full backup (2:00 AM)
0 2 * * * /backup/scripts/daily_full_backup.sh

# Hourly incremental backup (every hour except 2 AM)
0 1,3-23 * * * /backup/scripts/hourly_incremental_backup.sh

# Weekly verification (Sunday 3:00 AM)
0 3 * * 0 /backup/scripts/weekly_backup_verification.sh

# Monthly archive (1st day, 4:00 AM)
0 4 1 * * /backup/scripts/monthly_archive.sh
```

### Backup Locations
1. **Local Backup** - `/backup/local/` (7-day retention)
2. **Network Backup** - `backup-server:/backup/duration-system/` (30-day retention)
3. **Cloud Archive** - AWS S3/equivalent (1-year retention)
4. **Offsite Archive** - Physical media (3-year retention)

### Backup Content
```bash
# Full backup includes:
databases/
├── framework.db
├── task_timer.db
├── gdpr_compliance.db
└── retention_policies.db

application/
├── duration_system/
├── streamlit_extension/
├── tests/
├── pyproject.toml
└── configuration files

data/
├── epics/user_epics/
├── reports/
└── audit_logs/

security/
├── gdpr_audit.log
├── security.log
└── access_logs/
```

---

## 🔄 Recovery Procedures

### Database Recovery
```bash
#!/bin/bash
# Database recovery script

BACKUP_DATE=${1:-$(date +%Y%m%d)}
BACKUP_PATH="/backup/daily/$BACKUP_DATE"

echo "Starting database recovery from $BACKUP_DATE..."

# Verify backup integrity
if ! sqlite3 "$BACKUP_PATH/framework.db" "PRAGMA integrity_check;"; then
    echo "ERROR: Backup database corrupted"
    exit 1
fi

# Stop services
pkill -f streamlit

# Backup current corrupted database
mkdir -p /backup/corrupted/$(date +%Y%m%d_%H%M%S)
cp framework.db /backup/corrupted/$(date +%Y%m%d_%H%M%S)/ 2>/dev/null

# Restore databases
cp "$BACKUP_PATH/framework.db" ./
cp "$BACKUP_PATH/task_timer.db" ./
cp "$BACKUP_PATH/gdpr_compliance.db" ./

# Set proper permissions
chmod 644 *.db

# Verify restoration
python test_database_integrity.py

# Apply any incremental changes
if [ -f "/backup/incremental/changes_since_$BACKUP_DATE.sql" ]; then
    sqlite3 framework.db < "/backup/incremental/changes_since_$BACKUP_DATE.sql"
fi

echo "Database recovery completed successfully"
```

### Application Recovery
```bash
#!/bin/bash
# Application recovery script

BACKUP_DATE=${1:-$(date +%Y%m%d)}
BACKUP_PATH="/backup/daily/$BACKUP_DATE"

echo "Starting application recovery from $BACKUP_DATE..."

# Create recovery environment
mkdir -p /recovery/duration-system
cd /recovery/duration-system

# Restore application code
rsync -av "$BACKUP_PATH/application/" ./

# Install dependencies
python -m pip install -e .

# Restore configuration
cp "$BACKUP_PATH/config/"* ./

# Verify installation
python -c "import duration_system; print('✓ Duration system import successful')"

# Run basic tests
python -m pytest tests/basic_functionality.py

echo "Application recovery completed successfully"
```

---

## 📊 Monitoring & Alerting

### Health Check Monitoring
```python
#!/usr/bin/env python3
# health_monitor.py - Continuous system health monitoring

import time
import sqlite3
import psutil
import logging
from pathlib import Path
from datetime import datetime

class DisasterPreventionMonitor:
    def __init__(self):
        self.logger = logging.getLogger('disaster.prevention')
        self.alert_thresholds = {
            'disk_usage': 85,      # %
            'memory_usage': 90,    # %
            'cpu_usage': 95,       # %
            'db_size_growth': 200, # MB per hour
            'error_rate': 10       # errors per minute
        }
    
    def check_database_health(self):
        """Check database integrity and performance."""
        try:
            # Check each database
            databases = ['framework.db', 'task_timer.db', 'gdpr_compliance.db']
            
            for db in databases:
                if not Path(db).exists():
                    self.alert(f"CRITICAL: Database {db} missing")
                    continue
                
                # Integrity check
                conn = sqlite3.connect(db)
                result = conn.execute("PRAGMA integrity_check;").fetchone()
                if result[0] != "ok":
                    self.alert(f"CRITICAL: Database {db} integrity compromised")
                
                # Size monitoring
                size_mb = Path(db).stat().st_size / (1024 * 1024)
                if size_mb > 1000:  # Alert if DB > 1GB
                    self.alert(f"WARNING: Database {db} size: {size_mb:.1f}MB")
                
                conn.close()
            
        except Exception as e:
            self.alert(f"ERROR: Database health check failed: {e}")
    
    def check_system_resources(self):
        """Monitor system resource usage."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > self.alert_thresholds['cpu_usage']:
            self.alert(f"HIGH CPU: {cpu_percent}%")
        
        # Memory usage
        memory = psutil.virtual_memory()
        if memory.percent > self.alert_thresholds['memory_usage']:
            self.alert(f"HIGH MEMORY: {memory.percent}%")
        
        # Disk usage
        disk = psutil.disk_usage('.')
        disk_percent = (disk.used / disk.total) * 100
        if disk_percent > self.alert_thresholds['disk_usage']:
            self.alert(f"HIGH DISK: {disk_percent:.1f}%")
    
    def alert(self, message):
        """Send alert notification."""
        timestamp = datetime.now().isoformat()
        alert_msg = f"[{timestamp}] DISASTER ALERT: {message}"
        
        # Log alert
        self.logger.error(alert_msg)
        
        # In production, also send to:
        # - Email notifications
        # - Slack/Teams channels
        # - SMS for critical alerts
        # - Monitoring dashboard
        
        print(alert_msg)
    
    def run_continuous_monitoring(self):
        """Run continuous health monitoring."""
        while True:
            try:
                self.check_database_health()
                self.check_system_resources()
                time.sleep(300)  # Check every 5 minutes
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

if __name__ == "__main__":
    monitor = DisasterPreventionMonitor()
    monitor.run_continuous_monitoring()
```

---

## 🧪 Testing & Validation

### Monthly Disaster Recovery Drill
```bash
#!/bin/bash
# monthly_dr_drill.sh - Monthly disaster recovery testing

echo "=== DISASTER RECOVERY DRILL - $(date) ==="

# 1. Simulate database corruption
echo "Step 1: Simulating database corruption..."
cp framework.db framework.db.original
echo "CORRUPT" >> framework.db

# 2. Test detection
echo "Step 2: Testing corruption detection..."
if python test_database_integrity.py | grep -q "FAILED"; then
    echo "✓ Corruption detected successfully"
else
    echo "✗ Corruption detection failed"
    exit 1
fi

# 3. Test recovery procedure
echo "Step 3: Testing recovery procedure..."
if ./disaster_recovery/database_recovery.sh; then
    echo "✓ Database recovery successful"
else
    echo "✗ Database recovery failed"
    exit 1
fi

# 4. Test service restoration
echo "Step 4: Testing service restoration..."
python -m streamlit run dashboard.py --server.port 8502 &
STREAMLIT_PID=$!
sleep 10

if curl -s http://localhost:8502 > /dev/null; then
    echo "✓ Service restoration successful"
    kill $STREAMLIT_PID
else
    echo "✗ Service restoration failed"
    kill $STREAMLIT_PID
    exit 1
fi

# 5. Test data integrity
echo "Step 5: Testing data integrity..."
if python test_database_integrity.py | grep -q "All tests passed"; then
    echo "✓ Data integrity verified"
else
    echo "✗ Data integrity check failed"
    exit 1
fi

echo "=== DRILL COMPLETED SUCCESSFULLY ==="
```

### Recovery Time Testing
```python
#!/usr/bin/env python3
# recovery_time_test.py - Measure actual recovery times

import time
import subprocess
import sqlite3
from datetime import datetime

def measure_recovery_time():
    """Measure actual recovery times for different scenarios."""
    
    results = {}
    
    # Test 1: Database corruption recovery
    start_time = time.time()
    
    # Corrupt database
    with open('framework.db', 'ab') as f:
        f.write(b'CORRUPT_DATA')
    
    # Run recovery
    subprocess.run(['./disaster_recovery/database_recovery.sh'], 
                  capture_output=True)
    
    # Verify recovery
    conn = sqlite3.connect('framework.db')
    conn.execute("SELECT COUNT(*) FROM framework_epics")
    conn.close()
    
    results['database_recovery'] = time.time() - start_time
    
    # Test 2: Full system restoration
    start_time = time.time()
    
    # Simulate system failure
    subprocess.run(['pkill', '-f', 'streamlit'])
    
    # Run restoration
    subprocess.run(['./disaster_recovery/full_system_restore.sh'],
                  capture_output=True)
    
    results['full_restoration'] = time.time() - start_time
    
    print("Recovery Time Measurements:")
    for test, duration in results.items():
        print(f"  {test}: {duration:.2f} seconds")
        
        # Check against RTO requirements
        if test == 'database_recovery' and duration > 7200:  # 2 hours
            print(f"  ⚠️  {test} exceeds RTO requirement")
        elif test == 'full_restoration' and duration > 14400:  # 4 hours
            print(f"  ⚠️  {test} exceeds RTO requirement")
        else:
            print(f"  ✓ {test} meets RTO requirement")

if __name__ == "__main__":
    measure_recovery_time()
```

---

## 📞 Emergency Contacts

### Primary Response Team
- **Technical Lead:** [Name] - [Phone] - [Email]
- **Security Officer:** [Name] - [Phone] - [Email]
- **Database Admin:** [Name] - [Phone] - [Email]
- **Operations Manager:** [Name] - [Phone] - [Email]

### Escalation Chain
1. **Incident Commander** (0-2 hours)
2. **Engineering Manager** (2-4 hours)
3. **CTO/Technical Director** (4+ hours)
4. **External Consultants** (if required)

### External Contacts
- **Cloud Provider Support:** [Support Number]
- **Internet Service Provider:** [Support Number]
- **Hardware Vendor:** [Support Number]
- **Legal/Compliance:** [Contact Info]

---

## 📚 Documentation & Training

### Required Training
1. **Annual DR Training** - All technical staff
2. **Quarterly Drill Participation** - Response team
3. **Monthly Backup Verification** - Database admins
4. **Incident Response Procedures** - All staff

### Documentation Updates
- Review and update plan quarterly
- Update after any significant system changes
- Update contact information monthly
- Version control all changes

---

## ✅ Compliance & Regulatory

### Regulatory Requirements
- **GDPR Article 32** - Security of processing
- **ISO 27001** - Information security management
- **SOC 2 Type II** - Security controls
- **Industry Standards** - As applicable

### Audit Trail
- All disaster recovery activities logged
- Regular compliance assessments
- External audit requirements met
- Documentation retention policies followed

---

## 📈 Continuous Improvement

### Post-Incident Review Process
1. **Immediate After-Action Report** (within 24 hours)
2. **Detailed Analysis** (within 1 week)
3. **Process Improvements** (within 2 weeks)
4. **Plan Updates** (within 1 month)

### Performance Metrics
- **Mean Time to Detection (MTTD)**
- **Mean Time to Recovery (MTTR)**
- **Recovery Point Objective (RPO) compliance**
- **Recovery Time Objective (RTO) compliance**

---

**Document Control:**
- **Next Review Date:** 2025-11-13
- **Approved By:** Security Team
- **Distribution:** Technical Staff, Management
- **Classification:** CONFIDENTIAL