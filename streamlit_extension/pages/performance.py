"""
🚀 Performance Testing Dashboard

Streamlit interface for the performance testing system:
- Real-time performance monitoring
- Load testing execution
- Database performance analysis
- Performance report generation
- System metrics visualization
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
import threading

from streamlit_extension.utils.performance_tester import (
    PerformanceProfiler,
    DatabasePerformanceTester,
    LoadTester,
    PerformanceMonitor,
    PerformanceReporter,
    LoadTestConfig,
    run_quick_performance_check,
    create_performance_test_suite
)
from streamlit_extension.utils.database import DatabaseManager
from streamlit_extension.utils.exception_handler import handle_streamlit_exceptions

# Authentication middleware
try:
    from streamlit_extension.auth.middleware import init_protected_page
except ImportError:
    init_protected_page = None


# Page configuration
st.set_page_config(
    page_title="Performance Testing Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)


def initialize_performance_components():
    """Initialize performance testing components."""
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager("framework.db", "task_timer.db")
    
    if 'performance_monitor' not in st.session_state:
        st.session_state.performance_monitor = PerformanceMonitor()
    
    if 'performance_history' not in st.session_state:
        st.session_state.performance_history = []
    
    if 'monitoring_active' not in st.session_state:
        st.session_state.monitoring_active = False


@handle_streamlit_exceptions(show_error=True, attempt_recovery=True)
def render_performance_dashboard():
    """Render main performance dashboard."""
    # Initialize protected page with authentication
    current_user = init_protected_page("🚀 Performance Testing Dashboard")
    if not current_user:
        st.error("Authentication required")
        return
    
    st.markdown("Monitor system performance, run load tests, and analyze bottlenecks")
    
    # Sidebar controls
    render_sidebar_controls()
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Real-time Monitoring",
        "⚡ Load Testing", 
        "🗄️ Database Performance",
        "📈 Performance Analytics",
        "📋 Reports"
    ])
    
    with tab1:
        render_realtime_monitoring()
    
    with tab2:
        render_load_testing()
    
    with tab3:
        render_database_performance()
    
    with tab4:
        render_performance_analytics()
    
    with tab5:
        render_performance_reports()


def render_sidebar_controls():
    """Render sidebar performance controls."""
    st.sidebar.header("🎛️ Performance Controls")
    
    # System monitoring toggle
    if st.sidebar.button("Start/Stop Monitoring"):
        if st.session_state.monitoring_active:
            st.session_state.performance_monitor.stop_monitoring()
            st.session_state.monitoring_active = False
            st.sidebar.success("Monitoring stopped")
        else:
            st.session_state.performance_monitor.start_monitoring(interval_seconds=5)
            st.session_state.monitoring_active = True
            st.sidebar.success("Monitoring started")
    
    # Quick performance check
    if st.sidebar.button("Quick Performance Check"):
        with st.spinner("Running quick performance check..."):
            results = run_quick_performance_check(st.session_state.db_manager)
            st.session_state.last_quick_check = results
            st.sidebar.success("Quick check completed!")
    
    # Monitoring status
    status_color = "🟢" if st.session_state.monitoring_active else "🔴"
    st.sidebar.markdown(f"**Monitoring Status:** {status_color}")
    
    # Current system metrics
    st.sidebar.subheader("📊 Current Metrics")
    current_metrics = st.session_state.performance_monitor.get_current_metrics()
    
    st.sidebar.metric("CPU Usage", f"{current_metrics['cpu_percent']:.1f}%")
    st.sidebar.metric("Memory Usage", f"{current_metrics['memory_percent']:.1f}%")
    st.sidebar.metric("Active Threads", current_metrics['active_threads'])


def render_realtime_monitoring():
    """Render real-time performance monitoring tab."""
    st.header("📊 Real-time Performance Monitoring")
    
    # Auto-refresh option
    auto_refresh = st.checkbox("Auto-refresh (every 5 seconds)", value=False)
    
    if auto_refresh:
        time.sleep(5)
        st.rerun()
    
    # Get current metrics
    current_metrics = st.session_state.performance_monitor.get_current_metrics()
    
    # Current metrics cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "CPU Usage",
            f"{current_metrics['cpu_percent']:.1f}%",
            delta=None
        )
    
    with col2:
        st.metric(
            "Memory Usage", 
            f"{current_metrics['memory_percent']:.1f}%",
            delta=None
        )
    
    with col3:
        st.metric(
            "Available Memory",
            f"{current_metrics['memory_available']:.0f} MB",
            delta=None
        )
    
    with col4:
        st.metric(
            "Active Threads",
            current_metrics['active_threads'],
            delta=None
        )
    
    # Historical metrics charts
    metrics_history = st.session_state.performance_monitor.get_metrics_history(last_n=100)
    
    if metrics_history:
        df = pd.DataFrame(metrics_history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # CPU and Memory usage over time
        col1, col2 = st.columns(2)
        
        with col1:
            fig_cpu = px.line(
                df, 
                x='timestamp', 
                y='cpu_percent',
                title='CPU Usage Over Time',
                labels={'cpu_percent': 'CPU %', 'timestamp': 'Time'}
            )
            fig_cpu.update_layout(height=300)
            st.plotly_chart(fig_cpu, use_container_width=True)
        
        with col2:
            fig_memory = px.line(
                df, 
                x='timestamp', 
                y='memory_percent',
                title='Memory Usage Over Time',
                labels={'memory_percent': 'Memory %', 'timestamp': 'Time'}
            )
            fig_memory.update_layout(height=300)
            st.plotly_chart(fig_memory, use_container_width=True)
    
    else:
        st.info("Start monitoring to see historical data")


def render_load_testing():
    """Render load testing tab."""
    st.header("⚡ Load Testing")
    
    # Load test configuration
    st.subheader("🎛️ Test Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        concurrent_users = st.slider("Concurrent Users", 1, 50, 10)
        duration_seconds = st.slider("Duration (seconds)", 10, 300, 60)
    
    with col2:
        operations_per_second = st.slider("Target Ops/sec", 1, 500, 100)
        test_data_size = st.slider("Test Data Size", 100, 5000, 1000)
    
    # Test type selection
    test_type = st.selectbox(
        "Test Type",
        ["Client Creation", "Client Read", "Project Creation", "Epic Updates", "Custom Query"]
    )
    
    # Run load test button
    if st.button("🚀 Run Load Test", type="primary"):
        config = LoadTestConfig(
            concurrent_users=concurrent_users,
            duration_seconds=duration_seconds,
            operations_per_second=operations_per_second,
            test_data_size=test_data_size
        )
        
        with st.spinner(f"Running load test for {duration_seconds} seconds..."):
            load_tester = LoadTester(st.session_state.db_manager)
            
            # Define test function based on selection
            if test_type == "Client Creation":
                def test_function(data):
                    return st.session_state.db_manager.create_client(**data)
            elif test_type == "Client Read":
                def test_function(data):
                    return st.session_state.db_manager.get_clients(limit=10)
            else:
                def test_function(data):
                    return st.session_state.db_manager.get_clients(limit=5)
            
            results = load_tester.run_load_test(config, test_function)
            st.session_state.last_load_test = results
    
    # Display last test results
    if 'last_load_test' in st.session_state:
        st.subheader("📊 Last Test Results")
        results = st.session_state.last_load_test
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        execution = results.get("execution", {})
        performance = results.get("performance", {})
        
        with col1:
            st.metric(
                "Total Operations",
                execution.get("total_operations", 0)
            )
        
        with col2:
            st.metric(
                "Operations/sec",
                f"{execution.get('operations_per_second', 0):.1f}"
            )
        
        with col3:
            st.metric(
                "Success Rate",
                f"{execution.get('success_rate', 0):.1f}%"
            )
        
        with col4:
            response_time = performance.get("response_time", {})
            st.metric(
                "Avg Response Time",
                f"{response_time.get('avg', 0):.1f}ms"
            )
        
        # Bottlenecks
        bottlenecks = results.get("bottlenecks", [])
        if bottlenecks:
            st.subheader("⚠️ Identified Bottlenecks")
            for bottleneck in bottlenecks:
                st.warning(bottleneck)
        else:
            st.success("✅ No performance bottlenecks detected")
        
        # Detailed results
        with st.expander("📋 Detailed Results"):
            st.json(results)


def render_database_performance():
    """Render database performance tab."""
    st.header("🗄️ Database Performance Analysis")
    
    # Quick database check
    if st.button("🔍 Analyze Database Performance"):
        with st.spinner("Analyzing database performance..."):
            db_tester = DatabasePerformanceTester(st.session_state.db_manager)
            
            # CRUD benchmark
            crud_results = db_tester.benchmark_crud_operations(iterations=100)
            
            # Query performance
            query_results = db_tester.test_query_performance()
            
            st.session_state.db_performance = {
                "crud": crud_results,
                "queries": query_results,
                "timestamp": datetime.now().isoformat()
            }
    
    # Display database performance results
    if 'db_performance' in st.session_state:
        results = st.session_state.db_performance
        
        st.subheader("📊 CRUD Operations Performance")
        
        # CRUD metrics
        crud_data = []
        for operation, stats in results["crud"].items():
            response_time = stats.get("response_time", {})
            crud_data.append({
                "Operation": operation,
                "Avg Time (ms)": response_time.get("avg", 0),
                "P95 Time (ms)": response_time.get("p95", 0),
                "Success Rate (%)": stats.get("success_rate", 0)
            })
        
        if crud_data:
            df_crud = pd.DataFrame(crud_data)
            st.dataframe(df_crud, use_container_width=True)
            
            # CRUD performance chart
            fig_crud = px.bar(
                df_crud, 
                x="Operation", 
                y="Avg Time (ms)",
                title="CRUD Operations Average Response Time"
            )
            st.plotly_chart(fig_crud, use_container_width=True)
        
        st.subheader("📈 Query Performance")
        
        # Query metrics
        query_data = []
        for query_name, stats in results["queries"].items():
            response_time = stats.get("response_time", {})
            query_data.append({
                "Query": query_name,
                "Avg Time (ms)": response_time.get("avg", 0),
                "Rows Returned": stats.get("rows_returned", 0),
                "Success Rate (%)": stats.get("success_rate", 0)
            })
        
        if query_data:
            df_queries = pd.DataFrame(query_data)
            st.dataframe(df_queries, use_container_width=True)
            
            # Query performance chart
            fig_queries = px.bar(
                df_queries, 
                x="Query", 
                y="Avg Time (ms)",
                title="Query Performance Comparison"
            )
            st.plotly_chart(fig_queries, use_container_width=True)


def render_performance_analytics():
    """Render performance analytics tab."""
    st.header("📈 Performance Analytics")
    
    # Quick check results
    if 'last_quick_check' in st.session_state:
        st.subheader("⚡ Latest Quick Check")
        results = st.session_state.last_quick_check
        
        col1, col2 = st.columns(2)
        
        with col1:
            clients_stats = results.get("get_clients", {})
            response_time = clients_stats.get("response_time", {})
            st.metric(
                "Get Clients - Avg Time",
                f"{response_time.get('avg', 0):.1f}ms"
            )
        
        with col2:
            projects_stats = results.get("get_projects", {})
            response_time = projects_stats.get("response_time", {})
            st.metric(
                "Get Projects - Avg Time", 
                f"{response_time.get('avg', 0):.1f}ms"
            )
    
    # Performance trends
    st.subheader("📊 Performance Trends")
    
    # Placeholder for trend analysis
    st.info("Performance trend analysis will show here when more data is collected")
    
    # System resource usage
    st.subheader("💾 System Resources")
    
    # Create a sample resource usage chart
    if st.session_state.monitoring_active:
        metrics_history = st.session_state.performance_monitor.get_metrics_history(last_n=50)
        
        if metrics_history:
            df = pd.DataFrame(metrics_history)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Multi-metric chart
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['cpu_percent'],
                mode='lines',
                name='CPU %',
                line=dict(color='red')
            ))
            
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['memory_percent'],
                mode='lines',
                name='Memory %',
                line=dict(color='blue')
            ))
            
            fig.update_layout(
                title='System Resource Usage',
                xaxis_title='Time',
                yaxis_title='Usage %',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)


def render_performance_reports():
    """Render performance reports tab."""
    st.header("📋 Performance Reports")
    
    # Generate comprehensive report
    if st.button("📊 Generate Comprehensive Report"):
        with st.spinner("Generating comprehensive performance report..."):
            results = create_performance_test_suite(st.session_state.db_manager)
            
            # Generate report
            reporter = PerformanceReporter("performance_reports")
            report_file = reporter.generate_performance_report(results, "comprehensive_dashboard_test")
            
            st.session_state.last_report_file = report_file
            st.session_state.last_report_results = results
    
    # Display last report
    if 'last_report_results' in st.session_state:
        st.subheader("📊 Latest Comprehensive Report")
        
        results = st.session_state.last_report_results
        
        # Summary metrics
        st.subheader("📈 Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Test Categories", len(results))
        
        with col2:
            # Calculate average success rate
            success_rates = []
            for test_category, test_data in results.items():
                if isinstance(test_data, dict) and "success_rate" in test_data:
                    success_rates.append(test_data["success_rate"])
            
            avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0
            st.metric("Avg Success Rate", f"{avg_success_rate:.1f}%")
        
        with col3:
            # Report file location
            if 'last_report_file' in st.session_state:
                st.markdown(f"**Report File:** `{Path(st.session_state.last_report_file).name}`")
        
        # Test results breakdown
        st.subheader("🔍 Test Results Breakdown")
        
        for test_category, test_data in results.items():
            with st.expander(f"📊 {test_category.replace('_', ' ').title()}"):
                if isinstance(test_data, dict):
                    # Extract key metrics
                    if "response_time" in test_data:
                        response_time = test_data["response_time"]
                        st.write(f"**Average Response Time:** {response_time.get('avg', 0):.1f}ms")
                        st.write(f"**95th Percentile:** {response_time.get('p95', 0):.1f}ms")
                    
                    if "success_rate" in test_data:
                        st.write(f"**Success Rate:** {test_data['success_rate']:.1f}%")
                    
                    if "total_operations" in test_data:
                        st.write(f"**Total Operations:** {test_data['total_operations']}")
                    
                    # Show full data
                    st.json(test_data)
                else:
                    st.write(test_data)
    
    # Historical reports
    st.subheader("📚 Historical Reports")
    
    reports_dir = Path("performance_reports")
    if reports_dir.exists():
        report_files = list(reports_dir.glob("*.json"))
        
        if report_files:
            selected_report = st.selectbox(
                "Select Report",
                options=[f.name for f in sorted(report_files, reverse=True)],
                help="Select a historical performance report to view"
            )
            
            if selected_report:
                selected_path = reports_dir / selected_report
                
                try:
                    with open(selected_path) as f:
                        report_data = json.load(f)
                    
                    st.write(f"**Report:** {report_data.get('test_name', 'Unknown')}")
                    st.write(f"**Generated:** {report_data.get('timestamp', 'Unknown')}")
                    
                    with st.expander("📋 Full Report Data"):
                        st.json(report_data)
                
                except Exception as e:
                    st.error(f"Error loading report: {e}")
        else:
            st.info("No historical reports found")
    else:
        st.info("Reports directory not found")


def main():
    """Main performance dashboard function."""
    try:
        initialize_performance_components()
        render_performance_dashboard()
        
    except Exception as e:
        st.error(f"Error in performance dashboard: {e}")
        st.exception(e)


if __name__ == "__main__":
    main()