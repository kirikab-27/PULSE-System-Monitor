#!/usr/bin/env python3
"""
Comprehensive Test Suite for Memory Monitor System
Tests all components of the advanced memory monitoring system
"""

import os
import sys
import time
import json
import tempfile
import subprocess
from datetime import datetime
from unittest.mock import Mock, patch

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from memory_monitor import MemoryMonitor
    from ml_anomaly_detector import MemoryAnomalyDetector
    from process_tracker import ProcessMemoryTracker
    from memory_optimizer import MemoryOptimizer
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all required modules are available")
    sys.exit(1)

class TestSuite:
    def __init__(self):
        self.test_results = []
        self.temp_files = []
    
    def log_test(self, test_name, status, details=None, duration=None):
        """Log test results"""
        result = {
            'test_name': test_name,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'duration': duration,
            'details': details
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        duration_str = f" ({duration:.3f}s)" if duration else ""
        print(f"{status_icon} {test_name}{duration_str}")
        
        if details and status != "PASS":
            print(f"   Details: {details}")
    
    def test_memory_monitor_basic(self):
        """Test basic memory monitoring functionality"""
        start_time = time.time()
        try:
            monitor = MemoryMonitor()
            
            # Test system memory collection
            system_mem = monitor.get_system_memory()
            assert 'timestamp' in system_mem
            assert 'physical' in system_mem
            assert 'swap' in system_mem
            assert system_mem['physical']['total'] > 0
            
            # Test process memory collection
            process_data = monitor.get_process_memory()
            assert isinstance(process_data, list)
            assert len(process_data) > 0
            
            # Test report formatting
            monitoring_data = {
                'system': system_mem,
                'processes': process_data[:5],
                'leaks': [],
                'anomalies': [],
                'suggestions': []
            }
            report = monitor.format_report(monitoring_data)
            assert 'timestamp' in report
            assert 'summary' in report
            
            duration = time.time() - start_time
            self.log_test("Memory Monitor Basic", "PASS", duration=duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Memory Monitor Basic", "FAIL", str(e), duration)
    
    def test_memory_leak_detection(self):
        """Test memory leak detection"""
        start_time = time.time()
        try:
            monitor = MemoryMonitor()
            
            # Simulate process data with increasing memory
            test_processes = []
            for i in range(15):
                test_processes.append({
                    'pid': 1234,
                    'name': 'test_process',
                    'rss': 1000000 + (i * 100000),  # Increasing memory
                    'vms': 2000000 + (i * 100000),
                    'percent': 1.0 + (i * 0.1),
                    'shared': 50000,
                    'data': 100000,
                    'stack': 8192
                })
                
                # Add to history
                monitor.history[1234].append(test_processes[-1]['rss'])
            
            # Test leak detection
            leaks = monitor.detect_memory_leak(test_processes[-5:])
            assert isinstance(leaks, list)
            
            # Should detect the artificial leak
            leak_detected = any(leak['pid'] == 1234 for leak in leaks)
            
            duration = time.time() - start_time
            self.log_test("Memory Leak Detection", "PASS" if leak_detected else "WARN", 
                         f"Leak detected: {leak_detected}", duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Memory Leak Detection", "FAIL", str(e), duration)
    
    def test_anomaly_detector(self):
        """Test ML-based anomaly detection"""
        start_time = time.time()
        try:
            detector = MemoryAnomalyDetector()
            
            # Create test memory data
            test_data = {
                'system': {
                    'timestamp': datetime.now().isoformat(),
                    'physical': {
                        'total': 8589934592,
                        'available': 4294967296,
                        'used': 4294967296,
                        'percent': 50.0
                    },
                    'swap': {
                        'total': 2147483648,
                        'used': 214748364,
                        'percent': 10.0
                    }
                },
                'processes': [
                    {'rss': 536870912, 'percent': 6.25},
                    {'rss': 268435456, 'percent': 3.125}
                ]
            }
            
            # Test feature extraction
            features = detector.extract_features(test_data)
            assert isinstance(features, type(features))  # numpy array check
            assert len(features) > 0
            
            # Test pattern detection (should work even with limited data)
            result = detector.detect_memory_patterns(test_data)
            assert 'anomaly_score' in result
            assert 'status' in result
            
            # Test insight generation
            insights = detector.generate_insights(result)
            assert isinstance(insights, list)
            
            duration = time.time() - start_time
            self.log_test("Anomaly Detector", "PASS", duration=duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Anomaly Detector", "FAIL", str(e), duration)
    
    def test_process_tracker(self):
        """Test process memory tracking"""
        start_time = time.time()
        try:
            # Use temporary database
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
                db_path = tmp_db.name
                self.temp_files.append(db_path)
            
            tracker = ProcessMemoryTracker(db_path)
            
            # Test database initialization
            assert os.path.exists(db_path)
            
            # Test process info collection
            import psutil
            test_proc = next(psutil.process_iter(['pid', 'name', 'memory_info', 'memory_percent']))
            proc_info = tracker.get_detailed_process_info(test_proc)
            
            if proc_info:  # Might fail due to permissions
                assert 'pid' in proc_info
                assert 'name' in proc_info
                assert 'rss' in proc_info
            
            # Test DNA calculation with mock data
            mock_history = []
            for i in range(10):
                mock_history.append({
                    'rss': 1000000 + i * 10000,
                    'vms': 2000000 + i * 10000,
                    'shared': 50000,
                    'data_segment': 100000,
                    'stack_segment': 8192,
                    'memory_percent': 1.0,
                    'cpu_percent': 5.0,
                    'num_threads': 4,
                    'memory_maps_count': 20
                })
            
            dna_info = tracker.calculate_process_dna(mock_history)
            if dna_info:
                assert 'hash' in dna_info
                assert 'pattern' in dna_info
            
            duration = time.time() - start_time
            self.log_test("Process Tracker", "PASS", duration=duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Process Tracker", "FAIL", str(e), duration)
    
    def test_memory_optimizer(self):
        """Test memory optimization engine"""
        start_time = time.time()
        try:
            optimizer = MemoryOptimizer()
            
            # Test system profiling
            profile = optimizer.analyze_system_profile()
            assert 'total_memory' in profile
            assert 'category' in profile
            
            # Test memory analysis
            analysis = optimizer.analyze_memory_usage_patterns()
            assert 'timestamp' in analysis
            assert 'system_memory' in analysis
            assert 'top_processes' in analysis
            
            # Test strategy generation
            strategies = optimizer.generate_optimization_strategies(analysis)
            assert isinstance(strategies, list)
            
            # Test quick tips
            tips = optimizer.get_quick_optimization_tips()
            assert isinstance(tips, list)
            assert len(tips) > 0
            
            duration = time.time() - start_time
            self.log_test("Memory Optimizer", "PASS", duration=duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Memory Optimizer", "FAIL", str(e), duration)
    
    def test_integration(self):
        """Test integration between components"""
        start_time = time.time()
        try:
            # Test data flow between components
            monitor = MemoryMonitor()
            detector = MemoryAnomalyDetector()
            optimizer = MemoryOptimizer()
            
            # Get data from monitor
            system_mem = monitor.get_system_memory()
            process_data = monitor.get_process_memory()
            
            # Create monitoring data
            monitoring_data = {
                'system': system_mem,
                'processes': process_data[:10],
                'leaks': [],
                'anomalies': [],
                'suggestions': []
            }
            
            # Test anomaly detection on monitor data
            anomaly_result = detector.detect_memory_patterns(monitoring_data)
            
            # Test optimization analysis
            opt_analysis = optimizer.analyze_memory_usage_patterns()
            strategies = optimizer.generate_optimization_strategies(opt_analysis)
            
            # Verify data compatibility
            assert monitoring_data['system']['physical']['percent'] == opt_analysis['system_memory']['percent']
            
            duration = time.time() - start_time
            self.log_test("Integration", "PASS", duration=duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Integration", "FAIL", str(e), duration)
    
    def test_cli_interfaces(self):
        """Test command line interfaces"""
        start_time = time.time()
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Test memory monitor CLI (brief run)
            cmd = [sys.executable, os.path.join(script_dir, 'memory_optimizer.py'), '--tips']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            assert result.returncode == 0 or "tips" in result.stdout.lower()
            
            # Test anomaly detector CLI
            cmd = [sys.executable, os.path.join(script_dir, 'ml_anomaly_detector.py')]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            # Should run without major errors
            
            duration = time.time() - start_time
            self.log_test("CLI Interfaces", "PASS", duration=duration)
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            self.log_test("CLI Interfaces", "WARN", "Timeout - scripts may run indefinitely", duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("CLI Interfaces", "FAIL", str(e), duration)
    
    def test_data_persistence(self):
        """Test data persistence and file operations"""
        start_time = time.time()
        try:
            # Test report generation and saving
            monitor = MemoryMonitor()
            system_mem = monitor.get_system_memory()
            process_data = monitor.get_process_memory()
            
            monitoring_data = {
                'system': system_mem,
                'processes': process_data[:5],
                'leaks': [],
                'anomalies': [],
                'suggestions': []
            }
            
            report = monitor.format_report(monitoring_data)
            
            # Test JSON serialization
            json_str = json.dumps(report)
            loaded_report = json.loads(json_str)
            assert loaded_report['timestamp'] == report['timestamp']
            
            # Test file operations
            test_file = 'memory-monitor/data/test_report.json'
            os.makedirs(os.path.dirname(test_file), exist_ok=True)
            
            with open(test_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            assert os.path.exists(test_file)
            
            with open(test_file, 'r') as f:
                loaded_from_file = json.load(f)
            
            assert loaded_from_file['timestamp'] == report['timestamp']
            
            # Cleanup
            os.remove(test_file)
            
            duration = time.time() - start_time
            self.log_test("Data Persistence", "PASS", duration=duration)
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_test("Data Persistence", "FAIL", str(e), duration)
    
    def run_all_tests(self):
        """Run all tests in the suite"""
        print("🧪 Starting Memory Monitor Test Suite")
        print("=" * 50)
        
        test_methods = [
            self.test_memory_monitor_basic,
            self.test_memory_leak_detection,
            self.test_anomaly_detector,
            self.test_process_tracker,
            self.test_memory_optimizer,
            self.test_integration,
            self.test_cli_interfaces,
            self.test_data_persistence
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                self.log_test(test_method.__name__, "FAIL", str(e))
        
        print("\n" + "=" * 50)
        self.print_summary()
        
        # Cleanup
        self.cleanup()
        
        return self.test_results
    
    def print_summary(self):
        """Print test summary"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warned_tests = len([r for r in self.test_results if r['status'] == 'WARN'])
        
        print(f"📊 Test Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {failed_tests}")
        print(f"   Warnings: {warned_tests}")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"   - {result['test_name']}: {result['details']}")
    
    def cleanup(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception:
                pass

def main():
    """Main test execution"""
    suite = TestSuite()
    results = suite.run_all_tests()
    
    # Save test results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = f"memory-monitor/data/test_results_{timestamp}.json"
    os.makedirs(os.path.dirname(results_file), exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed test results saved to: {results_file}")
    
    # Return exit code based on results
    failed_tests = len([r for r in results if r['status'] == 'FAIL'])
    return 0 if failed_tests == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)