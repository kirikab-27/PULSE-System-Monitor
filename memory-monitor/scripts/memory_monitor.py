#!/usr/bin/env python3
"""
Advanced Memory Monitor with AI-driven anomaly detection
Implements innovative memory monitoring techniques
"""

import os
import time
import json
import psutil
import numpy as np
from datetime import datetime
from collections import defaultdict, deque
import warnings
warnings.filterwarnings('ignore')

class MemoryMonitor:
    def __init__(self):
        self.history = defaultdict(lambda: deque(maxlen=100))
        self.process_patterns = {}
        self.anomaly_threshold = 2.0  # Standard deviations
        
    def get_system_memory(self):
        """Get detailed system memory information"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'physical': {
                'total': mem.total,
                'available': mem.available,
                'used': mem.used,
                'percent': mem.percent,
                'active': getattr(mem, 'active', 0),
                'inactive': getattr(mem, 'inactive', 0),
                'buffers': getattr(mem, 'buffers', 0),
                'cached': getattr(mem, 'cached', 0),
                'shared': getattr(mem, 'shared', 0)
            },
            'swap': {
                'total': swap.total,
                'used': swap.used,
                'free': swap.free,
                'percent': swap.percent,
                'sin': getattr(swap, 'sin', 0),
                'sout': getattr(swap, 'sout', 0)
            }
        }
    
    def get_process_memory(self):
        """Get memory usage for all processes"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'memory_percent']):
            try:
                pinfo = proc.info
                mem_info = pinfo['memory_info']
                processes.append({
                    'pid': pinfo['pid'],
                    'name': pinfo['name'],
                    'rss': mem_info.rss,  # Resident Set Size
                    'vms': mem_info.vms,  # Virtual Memory Size
                    'percent': pinfo['memory_percent'],
                    'shared': getattr(mem_info, 'shared', 0),
                    'data': getattr(mem_info, 'data', 0),
                    'stack': getattr(mem_info, 'stack', 0)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return sorted(processes, key=lambda x: x['rss'], reverse=True)
    
    def detect_memory_leak(self, process_data):
        """Detect potential memory leaks using pattern analysis"""
        leaks = []
        
        for proc in process_data[:20]:  # Check top 20 processes
            pid = proc['pid']
            rss = proc['rss']
            
            # Store historical data
            self.history[pid].append(rss)
            
            if len(self.history[pid]) >= 10:
                # Calculate trend
                data = np.array(list(self.history[pid]))
                x = np.arange(len(data))
                
                # Linear regression to detect increasing trend
                if len(data) > 1:
                    slope = np.polyfit(x, data, 1)[0]
                    avg_increase = slope / np.mean(data) * 100
                    
                    # Detect consistent memory growth
                    if avg_increase > 5:  # 5% average increase
                        leaks.append({
                            'pid': pid,
                            'name': proc['name'],
                            'growth_rate': f"{avg_increase:.2f}%",
                            'current_memory': rss,
                            'risk_level': 'HIGH' if avg_increase > 10 else 'MEDIUM'
                        })
        
        return leaks
    
    def calculate_memory_fingerprint(self, proc):
        """Create unique memory usage pattern for each process"""
        fingerprint = {
            'memory_ratio': proc['rss'] / proc['vms'] if proc['vms'] > 0 else 0,
            'shared_ratio': proc['shared'] / proc['rss'] if proc['rss'] > 0 else 0,
            'data_ratio': proc['data'] / proc['rss'] if proc['rss'] > 0 else 0,
            'stack_ratio': proc['stack'] / proc['rss'] if proc['rss'] > 0 else 0
        }
        return fingerprint
    
    def detect_anomalies(self, current_data):
        """Detect anomalies in memory usage patterns"""
        anomalies = []
        
        for proc in current_data[:50]:  # Analyze top 50 processes
            pid = proc['pid']
            fingerprint = self.calculate_memory_fingerprint(proc)
            
            # Initialize or update pattern
            if pid not in self.process_patterns:
                self.process_patterns[pid] = {
                    'samples': [],
                    'name': proc['name']
                }
            
            patterns = self.process_patterns[pid]['samples']
            patterns.append(fingerprint)
            
            # Keep only recent samples
            if len(patterns) > 20:
                patterns.pop(0)
            
            # Detect anomalies after sufficient samples
            if len(patterns) >= 5:
                # Calculate statistics for each metric
                for metric in fingerprint:
                    values = [p[metric] for p in patterns[:-1]]  # Exclude current
                    if values:
                        mean = np.mean(values)
                        std = np.std(values)
                        
                        if std > 0:
                            z_score = abs(fingerprint[metric] - mean) / std
                            
                            if z_score > self.anomaly_threshold:
                                anomalies.append({
                                    'pid': pid,
                                    'name': proc['name'],
                                    'metric': metric,
                                    'z_score': z_score,
                                    'current_value': fingerprint[metric],
                                    'expected_range': f"{mean:.3f} ± {std:.3f}",
                                    'severity': 'HIGH' if z_score > 3 else 'MEDIUM'
                                })
        
        return anomalies
    
    def generate_optimization_suggestions(self, system_mem, process_data):
        """Generate memory optimization suggestions"""
        suggestions = []
        
        # System-level suggestions
        if system_mem['physical']['percent'] > 80:
            suggestions.append({
                'type': 'SYSTEM',
                'priority': 'HIGH',
                'issue': f"High memory usage: {system_mem['physical']['percent']:.1f}%",
                'suggestion': 'Consider increasing physical memory or optimizing running applications'
            })
        
        if system_mem['swap']['percent'] > 50:
            suggestions.append({
                'type': 'SYSTEM',
                'priority': 'MEDIUM',
                'issue': f"High swap usage: {system_mem['swap']['percent']:.1f}%",
                'suggestion': 'Reduce memory pressure to improve system performance'
            })
        
        # Process-level suggestions
        total_mem = sum(p['rss'] for p in process_data)
        for proc in process_data[:10]:
            proc_percent = (proc['rss'] / total_mem) * 100
            if proc_percent > 20:
                suggestions.append({
                    'type': 'PROCESS',
                    'priority': 'MEDIUM',
                    'process': proc['name'],
                    'pid': proc['pid'],
                    'issue': f"Process using {proc_percent:.1f}% of total process memory",
                    'suggestion': 'Consider process optimization or resource limits'
                })
        
        # Cache optimization
        cache_ratio = system_mem['physical']['cached'] / system_mem['physical']['total']
        if cache_ratio < 0.1:
            suggestions.append({
                'type': 'CACHE',
                'priority': 'LOW',
                'issue': 'Low cache utilization',
                'suggestion': 'System may benefit from cache tuning'
            })
        
        return suggestions
    
    def format_report(self, data):
        """Format monitoring data into a structured report"""
        report = {
            'timestamp': data['system']['timestamp'],
            'summary': {
                'physical_usage': f"{data['system']['physical']['percent']:.1f}%",
                'swap_usage': f"{data['system']['swap']['percent']:.1f}%",
                'top_processes': len(data['processes']),
                'memory_leaks': len(data['leaks']),
                'anomalies': len(data['anomalies']),
                'suggestions': len(data['suggestions'])
            },
            'details': data
        }
        return report

def main():
    monitor = MemoryMonitor()
    
    print("🚀 Advanced Memory Monitor Started")
    print("=" * 60)
    
    while True:
        try:
            # Collect data
            system_mem = monitor.get_system_memory()
            process_data = monitor.get_process_memory()
            
            # Analyze
            leaks = monitor.detect_memory_leak(process_data)
            anomalies = monitor.detect_anomalies(process_data)
            suggestions = monitor.generate_optimization_suggestions(system_mem, process_data)
            
            # Prepare report
            monitoring_data = {
                'system': system_mem,
                'processes': process_data[:20],  # Top 20 processes
                'leaks': leaks,
                'anomalies': anomalies,
                'suggestions': suggestions
            }
            
            report = monitor.format_report(monitoring_data)
            
            # Display summary
            print(f"\n📊 Memory Status at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Physical Memory: {report['summary']['physical_usage']} | "
                  f"Swap: {report['summary']['swap_usage']}")
            
            if leaks:
                print(f"\n⚠️  Potential Memory Leaks Detected: {len(leaks)}")
                for leak in leaks[:3]:
                    print(f"  - {leak['name']} (PID: {leak['pid']}) - "
                          f"Growth: {leak['growth_rate']} - Risk: {leak['risk_level']}")
            
            if anomalies:
                print(f"\n🔍 Anomalies Detected: {len(anomalies)}")
                for anomaly in anomalies[:3]:
                    print(f"  - {anomaly['name']} (PID: {anomaly['pid']}) - "
                          f"{anomaly['metric']} - Severity: {anomaly['severity']}")
            
            if suggestions:
                print(f"\n💡 Optimization Suggestions: {len(suggestions)}")
                for suggestion in suggestions[:3]:
                    print(f"  - [{suggestion['priority']}] {suggestion['suggestion']}")
            
            # Save detailed report
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = f"memory-monitor/data/report_{timestamp}.json"
            os.makedirs(os.path.dirname(report_file), exist_ok=True)
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            print("\n" + "-" * 60)
            
            # Wait before next iteration
            time.sleep(30)  # Monitor every 30 seconds
            
        except KeyboardInterrupt:
            print("\n\n✋ Memory Monitor stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()