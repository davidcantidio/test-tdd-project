#!/usr/bin/env python3
"""
🧪 Test File Coordination System

Test script to verify file coordination manager works correctly
for preventing concurrent modifications between agents.

Features tested:
- File locking between multiple processes
- Sequential agent execution within same process
- Backup creation and recovery
- Deadlock prevention
- Process crash recovery
"""

import argparse
import json
import multiprocessing
import os
import tempfile
import time
from pathlib import Path
from typing import Dict, Any
import sys

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from file_coordination_manager import (
    FileCoordinationManager,
    LockType,
    safe_file_modification
)


def create_test_file(file_path: str, content: str = "# Test file content\nprint('Hello World')"):
    """Create a test Python file."""
    with open(file_path, 'w') as f:
        f.write(content)


def simulate_agent_work(file_path: str, agent_name: str, work_duration: float, project_root: str):
    """Simulate an agent working on a file."""
    print(f"🤖 {agent_name} starting work on {file_path}")
    
    manager = FileCoordinationManager(project_root)
    
    try:
        with manager.acquire_file_lock(file_path, agent_name, LockType.EXCLUSIVE) as lock_info:
            print(f"🔒 {agent_name} acquired lock on {file_path}")
            print(f"   Backup created: {lock_info.backup_path}")
            
            # Simulate work
            time.sleep(work_duration)
            
            # Simulate modification
            with open(file_path, 'a') as f:
                f.write(f"\n# Modified by {agent_name} at {time.time()}")
            
            # Record modification
            manager.record_modification(
                file_path=file_path,
                agent_name=agent_name,
                modification_type="test_modification",
                backup_path=lock_info.backup_path or "",
                success=True
            )
            
            print(f"✅ {agent_name} completed work on {file_path}")
            
    except Exception as e:
        print(f"❌ {agent_name} failed: {e}")
        return False
    
    print(f"🔓 {agent_name} released lock on {file_path}")
    return True


def test_sequential_execution(project_root: str):
    """Test sequential execution of multiple agents on same file."""
    print("\n🧪 Testing Sequential Execution (Same Process)")
    print("=" * 50)
    
    # Create test file
    test_file = Path(project_root) / "test_sequential.py"
    create_test_file(str(test_file))
    
    agents = ["IntelligentCodeAgent", "RefactoringEngine", "TDDWorkflowAgent"]
    
    # Execute agents sequentially
    for i, agent in enumerate(agents):
        print(f"\n[{i+1}/{len(agents)}] Executing {agent}")
        success = simulate_agent_work(str(test_file), agent, 1.0, project_root)
        if not success:
            print(f"❌ Sequential test failed at {agent}")
            return False
    
    print("\n✅ Sequential execution test completed successfully")
    return True


def test_concurrent_execution(project_root: str):
    """Test concurrent execution of multiple agents (different processes)."""
    print("\n🧪 Testing Concurrent Execution (Multiple Processes)")
    print("=" * 55)
    
    # Create test file
    test_file = Path(project_root) / "test_concurrent.py"
    create_test_file(str(test_file))
    
    agents = [
        ("Agent1", 2.0),  # agent_name, work_duration
        ("Agent2", 1.5),
        ("Agent3", 1.0)
    ]
    
    # Start processes concurrently
    processes = []
    for agent_name, duration in agents:
        p = multiprocessing.Process(
            target=simulate_agent_work,
            args=(str(test_file), agent_name, duration, project_root)
        )
        p.start()
        processes.append((p, agent_name))
        time.sleep(0.1)  # Small delay to ensure processes start in order
    
    # Wait for all processes to complete
    print(f"\n⏱️  Waiting for {len(processes)} processes to complete...")
    
    results = []
    for p, agent_name in processes:
        p.join(timeout=10)  # 10 second timeout
        if p.exitcode == 0:
            results.append((agent_name, True))
            print(f"✅ {agent_name} completed successfully")
        else:
            results.append((agent_name, False))
            print(f"❌ {agent_name} failed or timed out")
    
    success_count = len([r for r in results if r[1]])
    print(f"\n📊 Concurrent execution results: {success_count}/{len(results)} successful")
    
    return success_count == len(results)


def test_deadlock_prevention(project_root: str):
    """Test deadlock prevention with timeout."""
    print("\n🧪 Testing Deadlock Prevention")
    print("=" * 35)
    
    # Create test file
    test_file = Path(project_root) / "test_deadlock.py" 
    create_test_file(str(test_file))
    
    def long_running_agent():
        """Agent that holds lock for a long time."""
        try:
            success = simulate_agent_work(str(test_file), "LongRunningAgent", 5.0, project_root)
            return success
        except Exception as e:
            print(f"Long running agent error: {e}")
            return False
    
    def quick_agent():
        """Agent that tries to acquire lock quickly."""
        time.sleep(1)  # Let long agent acquire lock first
        try:
            success = simulate_agent_work(str(test_file), "QuickAgent", 0.5, project_root)
            return success
        except Exception as e:
            print(f"Quick agent error: {e}")
            return False
    
    # Start long running agent
    p1 = multiprocessing.Process(target=long_running_agent)
    p1.start()
    
    # Start quick agent that should wait
    p2 = multiprocessing.Process(target=quick_agent)
    p2.start()
    
    # Wait for both to complete
    p1.join(timeout=15)
    p2.join(timeout=15)
    
    success = (p1.exitcode == 0) and (p2.exitcode == 0)
    
    if success:
        print("✅ Deadlock prevention test passed")
    else:
        print("❌ Deadlock prevention test failed")
    
    return success


def test_crash_recovery(project_root: str):
    """Test recovery from process crashes."""
    print("\n🧪 Testing Crash Recovery")
    print("=" * 25)
    
    # Create test file
    test_file = Path(project_root) / "test_crash.py"
    create_test_file(str(test_file))
    
    manager = FileCoordinationManager(project_root)
    
    # Simulate a crashed process by manually inserting a lock record
    import sqlite3
    from datetime import datetime
    
    with sqlite3.connect(str(manager.db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO file_locks 
            (file_path, lock_type, process_id, thread_id, agent_name, acquired_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(test_file),
            LockType.EXCLUSIVE.value,
            99999,  # Non-existent process ID
            "main",
            "CrashedAgent",
            datetime.now().isoformat(),
            datetime.now().isoformat()  # Expired lock
        ))
        conn.commit()
    
    print("💀 Simulated crashed process lock inserted")
    
    # Try to acquire lock - should succeed by cleaning up dead process
    try:
        success = simulate_agent_work(str(test_file), "RecoveryAgent", 1.0, project_root)
        if success:
            print("✅ Crash recovery test passed - dead lock was cleaned up")
            return True
        else:
            print("❌ Crash recovery test failed")
            return False
    except Exception as e:
        print(f"❌ Crash recovery test failed: {e}")
        return False


def show_coordination_status(project_root: str):
    """Show current coordination status."""
    print("\n📊 File Coordination Status")
    print("=" * 30)
    
    manager = FileCoordinationManager(project_root)
    
    # Show active locks
    locks = manager.get_lock_status()
    if locks:
        print("🔒 Active Locks:")
        for file_path, file_locks in locks.items():
            print(f"   📄 {file_path}")
            for lock in file_locks:
                alive = "✅" if lock["process_alive"] else "💀"
                print(f"      {alive} {lock['agent_name']} ({lock['lock_type']}) PID:{lock['process_id']}")
    else:
        print("✅ No active locks")
    
    # Show recent modifications
    history = manager.get_modification_history()
    if history:
        print(f"\n📝 Recent Modifications (last 5):")
        for mod in history[:5]:
            status = "✅" if mod["success"] else "❌"
            file_name = Path(mod["file_path"]).name
            print(f"   {status} {mod['agent_name']} -> {file_name} ({mod['timestamp'][:19]})")
    else:
        print("📝 No recent modifications")


def cleanup_test_files(project_root: str):
    """Clean up test files."""
    test_files = [
        "test_sequential.py",
        "test_concurrent.py", 
        "test_deadlock.py",
        "test_crash.py"
    ]
    
    for test_file in test_files:
        file_path = Path(project_root) / test_file
        if file_path.exists():
            file_path.unlink()
            print(f"🧹 Removed {test_file}")
    
    # Clean up coordination database
    db_path = Path(project_root) / ".file_coordination.db"
    if db_path.exists():
        db_path.unlink()
        print("🧹 Removed coordination database")
    
    # Clean up backup directory
    backup_dir = Path(project_root) / ".agent_backups"
    if backup_dir.exists():
        import shutil
        shutil.rmtree(backup_dir)
        print("🧹 Removed backup directory")


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(
        description="Test File Coordination System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Scenarios:
  --sequential     Test sequential agent execution (same process)
  --concurrent     Test concurrent agent execution (multiple processes)
  --deadlock       Test deadlock prevention with timeouts
  --crash-recovery Test recovery from crashed processes
  --status         Show current coordination status
  --cleanup        Clean up test files and database
  --all            Run all tests
        """
    )
    
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--sequential", action="store_true", help="Test sequential execution")
    parser.add_argument("--concurrent", action="store_true", help="Test concurrent execution")
    parser.add_argument("--deadlock", action="store_true", help="Test deadlock prevention")
    parser.add_argument("--crash-recovery", action="store_true", help="Test crash recovery")
    parser.add_argument("--status", action="store_true", help="Show coordination status")
    parser.add_argument("--cleanup", action="store_true", help="Clean up test files")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root).resolve()
    
    print(f"🧪 File Coordination System Test Suite")
    print(f"📁 Project Root: {project_root}")
    print(f"🕐 Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.cleanup:
        cleanup_test_files(str(project_root))
        return
    
    if args.status:
        show_coordination_status(str(project_root))
        return
    
    # Run tests
    test_results = {}
    
    if args.all or args.sequential:
        test_results["sequential"] = test_sequential_execution(str(project_root))
    
    if args.all or args.concurrent:
        test_results["concurrent"] = test_concurrent_execution(str(project_root))
    
    if args.all or args.deadlock:
        test_results["deadlock"] = test_deadlock_prevention(str(project_root))
    
    if args.all or args.crash_recovery:
        test_results["crash_recovery"] = test_crash_recovery(str(project_root))
    
    # Show final results
    if test_results:
        print(f"\n🎯 Final Test Results")
        print("=" * 25)
        
        passed = 0
        total = len(test_results)
        
        for test_name, success in test_results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"   {status} {test_name}")
            if success:
                passed += 1
        
        print(f"\n📊 Summary: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! File coordination system is working correctly.")
        else:
            print("⚠️  Some tests failed. Check output above for details.")
    
    # Always show final status
    show_coordination_status(str(project_root))


if __name__ == "__main__":
    main()