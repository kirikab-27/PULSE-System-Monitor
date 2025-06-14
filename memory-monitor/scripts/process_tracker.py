#!/usr/bin/env python3
"""
Advanced Process Memory Tracking with Time-series Analysis
Implements DNA fingerprinting for process memory patterns
"""

import os
import time
import json
import psutil
import hashlib
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
import sqlite3

class ProcessMemoryTracker:
    def __init__(self, db_path="memory-monitor/data/process_tracking.db"):
        self.db_path = db_path
        self.process_histories = defaultdict(lambda: deque(maxlen=200))
        self.process_dna = {}
        self.tracking_active = False
        self.lock = threading.Lock()
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for persistent storage"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS process_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    pid INTEGER,
                    name TEXT,
                    rss INTEGER,
                    vms INTEGER,
                    shared INTEGER,
                    data_segment INTEGER,
                    stack_segment INTEGER,
                    memory_percent REAL,
                    cpu_percent REAL,
                    num_threads INTEGER,
                    memory_maps_count INTEGER
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS process_dna (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pid INTEGER,
                    name TEXT,
                    dna_hash TEXT,
                    pattern_data TEXT,
                    created_at TEXT,
                    last_updated TEXT
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_process_memory_pid_time 
                ON process_memory(pid, timestamp)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_process_dna_pid 
                ON process_dna(pid)
            ''')
    
    def get_detailed_process_info(self, proc):
        """Get comprehensive process memory information"""
        try:
            pinfo = proc.info
            memory_info = pinfo['memory_info']
            
            # Get memory maps count
            try:
                memory_maps = len(proc.memory_maps())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                memory_maps = 0
            
            # Get additional memory details
            try:
                memory_full_info = proc.memory_full_info()
                shared = getattr(memory_full_info, 'shared', 0)
                data_segment = getattr(memory_full_info, 'data', 0)
                stack_segment = getattr(memory_full_info, 'stack', 0)
            except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
                shared = 0
                data_segment = 0
                stack_segment = 0
            
            return {
                'pid': pinfo['pid'],
                'name': pinfo['name'],
                'rss': memory_info.rss,
                'vms': memory_info.vms,
                'shared': shared,
                'data_segment': data_segment,
                'stack_segment': stack_segment,
                'memory_percent': pinfo.get('memory_percent', 0),
                'cpu_percent': pinfo.get('cpu_percent', 0),
                'num_threads': pinfo.get('num_threads', 0),
                'memory_maps_count': memory_maps,
                'timestamp': datetime.now().isoformat()
            }
        
        except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
            return None
    
    def calculate_process_dna(self, process_history):
        """Calculate unique DNA fingerprint for process memory behavior"""
        if len(process_history) < 5:
            return None
        
        # Extract feature vectors from history
        features = []
        for entry in process_history:
            if entry['rss'] > 0:  # Avoid division by zero
                features.append([
                    entry['rss'],
                    entry['vms'],
                    entry['shared'] / entry['rss'] if entry['rss'] > 0 else 0,
                    entry['data_segment'] / entry['rss'] if entry['rss'] > 0 else 0,
                    entry['stack_segment'] / entry['rss'] if entry['rss'] > 0 else 0,
                    entry['memory_percent'],
                    entry['cpu_percent'],
                    entry['num_threads'],
                    entry['memory_maps_count']
                ])
        
        if not features:
            return None
        
        # Calculate statistics for DNA pattern
        import numpy as np
        features_array = np.array(features)
        
        dna_pattern = {
            'mean_rss': float(np.mean(features_array[:, 0])),
            'std_rss': float(np.std(features_array[:, 0])),
            'mean_vms': float(np.mean(features_array[:, 1])),
            'std_vms': float(np.std(features_array[:, 1])),
            'avg_shared_ratio': float(np.mean(features_array[:, 2])),
            'avg_data_ratio': float(np.mean(features_array[:, 3])),
            'avg_stack_ratio': float(np.mean(features_array[:, 4])),
            'memory_variability': float(np.std(features_array[:, 5])),
            'cpu_correlation': float(np.corrcoef(features_array[:, 0], features_array[:, 6])[0, 1]) if len(features_array) > 1 else 0,
            'thread_stability': float(np.std(features_array[:, 7])),
            'map_count_avg': float(np.mean(features_array[:, 8])),
            'growth_rate': self.calculate_growth_rate(features_array[:, 0]),
            'pattern_complexity': self.calculate_pattern_complexity(features_array)
        }
        
        # Create DNA hash
        dna_string = json.dumps(dna_pattern, sort_keys=True)
        dna_hash = hashlib.md5(dna_string.encode()).hexdigest()
        
        return {
            'hash': dna_hash,
            'pattern': dna_pattern
        }
    
    def calculate_growth_rate(self, memory_values):
        """Calculate memory growth rate"""
        if len(memory_values) < 2:
            return 0.0
        
        # Simple linear regression
        import numpy as np
        x = np.arange(len(memory_values))
        slope = np.polyfit(x, memory_values, 1)[0]
        avg_memory = np.mean(memory_values)
        
        return float(slope / avg_memory) if avg_memory > 0 else 0.0
    
    def calculate_pattern_complexity(self, features_array):
        """Calculate complexity score of memory pattern"""
        import numpy as np
        
        # Measure variability across all features
        normalized_features = features_array / (np.max(features_array, axis=0) + 1e-10)
        complexity = np.mean(np.std(normalized_features, axis=0))
        
        return float(complexity)
    
    def track_processes(self, duration_minutes=None):
        """Start tracking all processes"""
        self.tracking_active = True
        start_time = time.time()
        
        print(f"🎯 Starting process memory tracking...")
        
        while self.tracking_active:
            try:
                # Get all processes with extended info
                processes = list(psutil.process_iter([
                    'pid', 'name', 'memory_info', 'memory_percent', 
                    'cpu_percent', 'num_threads'
                ]))
                
                timestamp = datetime.now().isoformat()
                batch_data = []
                
                for proc in processes:
                    proc_info = self.get_detailed_process_info(proc)
                    if proc_info:
                        pid = proc_info['pid']
                        
                        # Store in memory history
                        with self.lock:
                            self.process_histories[pid].append(proc_info)
                        
                        # Prepare for batch database insert
                        batch_data.append((
                            timestamp, pid, proc_info['name'],
                            proc_info['rss'], proc_info['vms'],
                            proc_info['shared'], proc_info['data_segment'],
                            proc_info['stack_segment'], proc_info['memory_percent'],
                            proc_info['cpu_percent'], proc_info['num_threads'],
                            proc_info['memory_maps_count']
                        ))
                        
                        # Update DNA pattern periodically
                        if len(self.process_histories[pid]) % 10 == 0:
                            self.update_process_dna(pid, proc_info['name'])
                
                # Batch insert to database
                if batch_data:
                    self.save_batch_to_db(batch_data)
                
                print(f"📊 Tracked {len(batch_data)} processes at {datetime.now().strftime('%H:%M:%S')}")
                
                # Check if duration limit reached
                if duration_minutes and (time.time() - start_time) > (duration_minutes * 60):
                    break
                
                time.sleep(10)  # Track every 10 seconds
                
            except KeyboardInterrupt:
                print("⏹️  Process tracking stopped by user")
                break
            except Exception as e:
                print(f"❌ Error in tracking: {e}")
                time.sleep(5)
        
        self.tracking_active = False
        print("✅ Process tracking completed")
    
    def save_batch_to_db(self, batch_data):
        """Save batch of process data to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.executemany('''
                    INSERT INTO process_memory 
                    (timestamp, pid, name, rss, vms, shared, data_segment, 
                     stack_segment, memory_percent, cpu_percent, num_threads, memory_maps_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', batch_data)
        except Exception as e:
            print(f"❌ Database error: {e}")
    
    def update_process_dna(self, pid, name):
        """Update DNA pattern for a specific process"""
        with self.lock:
            history = list(self.process_histories[pid])
        
        if len(history) < 5:
            return
        
        dna_info = self.calculate_process_dna(history)
        if not dna_info:
            return
        
        # Store DNA in database
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if DNA already exists
                cursor = conn.execute(
                    'SELECT id FROM process_dna WHERE pid = ?', (pid,)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing DNA
                    conn.execute('''
                        UPDATE process_dna 
                        SET dna_hash = ?, pattern_data = ?, last_updated = ?
                        WHERE pid = ?
                    ''', (dna_info['hash'], json.dumps(dna_info['pattern']), 
                          datetime.now().isoformat(), pid))
                else:
                    # Insert new DNA
                    conn.execute('''
                        INSERT INTO process_dna 
                        (pid, name, dna_hash, pattern_data, created_at, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (pid, name, dna_info['hash'], json.dumps(dna_info['pattern']),
                          datetime.now().isoformat(), datetime.now().isoformat()))
                
                # Store in memory cache
                self.process_dna[pid] = dna_info
        
        except Exception as e:
            print(f"❌ DNA update error: {e}")
    
    def detect_memory_anomalies(self, pid):
        """Detect anomalies in process memory behavior"""
        if pid not in self.process_dna:
            return {"status": "insufficient_data", "anomalies": []}
        
        dna_pattern = self.process_dna[pid]['pattern']
        
        with self.lock:
            recent_history = list(self.process_histories[pid])[-10:]
        
        if len(recent_history) < 5:
            return {"status": "insufficient_recent_data", "anomalies": []}
        
        anomalies = []
        
        # Check for memory leaks
        if dna_pattern['growth_rate'] > 0.05:  # 5% growth rate
            anomalies.append({
                'type': 'MEMORY_LEAK',
                'severity': 'HIGH' if dna_pattern['growth_rate'] > 0.1 else 'MEDIUM',
                'growth_rate': f"{dna_pattern['growth_rate']*100:.2f}%",
                'description': 'Consistent memory growth detected'
            })
        
        # Check for unusual memory patterns
        recent_rss = [entry['rss'] for entry in recent_history]
        if recent_rss:
            import numpy as np
            current_avg = np.mean(recent_rss)
            expected_avg = dna_pattern['mean_rss']
            
            if abs(current_avg - expected_avg) > 2 * dna_pattern['std_rss']:
                anomalies.append({
                    'type': 'UNUSUAL_MEMORY_USAGE',
                    'severity': 'MEDIUM',
                    'current_avg': int(current_avg),
                    'expected_avg': int(expected_avg),
                    'deviation': f"{abs(current_avg - expected_avg) / expected_avg * 100:.1f}%",
                    'description': 'Memory usage deviates from established pattern'
                })
        
        # Check thread stability
        if dna_pattern['thread_stability'] > 5:  # High thread count variation
            anomalies.append({
                'type': 'THREAD_INSTABILITY',
                'severity': 'LOW',
                'thread_variation': dna_pattern['thread_stability'],
                'description': 'Unstable thread count pattern'
            })
        
        return {
            'status': 'analyzed',
            'anomalies': anomalies,
            'dna_hash': self.process_dna[pid]['hash']
        }
    
    def get_process_summary(self, pid):
        """Get comprehensive summary for a process"""
        if pid not in self.process_histories:
            return None
        
        with self.lock:
            history = list(self.process_histories[pid])
        
        if not history:
            return None
        
        latest = history[-1]
        
        # Calculate statistics
        rss_values = [entry['rss'] for entry in history]
        import numpy as np
        
        summary = {
            'pid': pid,
            'name': latest['name'],
            'current_memory': {
                'rss': latest['rss'],
                'vms': latest['vms'],
                'shared': latest['shared'],
                'percent': latest['memory_percent']
            },
            'statistics': {
                'avg_rss': int(np.mean(rss_values)),
                'max_rss': int(np.max(rss_values)),
                'min_rss': int(np.min(rss_values)),
                'std_rss': int(np.std(rss_values)),
                'sample_count': len(history)
            },
            'dna_available': pid in self.process_dna,
            'last_updated': latest['timestamp']
        }
        
        # Add anomaly detection results
        if pid in self.process_dna:
            anomaly_results = self.detect_memory_anomalies(pid)
            summary['anomalies'] = anomaly_results
        
        return summary
    
    def generate_tracking_report(self):
        """Generate comprehensive tracking report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'tracking_status': 'active' if self.tracking_active else 'inactive',
            'total_processes_tracked': len(self.process_histories),
            'processes_with_dna': len(self.process_dna),
            'summary': []
        }
        
        # Get top memory consumers
        top_processes = []
        for pid, history in self.process_histories.items():
            if history:
                latest = history[-1]
                top_processes.append((pid, latest['name'], latest['rss']))
        
        # Sort by memory usage
        top_processes.sort(key=lambda x: x[2], reverse=True)
        
        # Generate summaries for top 10 processes
        for pid, name, rss in top_processes[:10]:
            summary = self.get_process_summary(pid)
            if summary:
                report['summary'].append(summary)
        
        return report
    
    def stop_tracking(self):
        """Stop the tracking process"""
        self.tracking_active = False

# CLI interface for the tracker
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Advanced Process Memory Tracker')
    parser.add_argument('--duration', type=int, help='Tracking duration in minutes')
    parser.add_argument('--report', action='store_true', help='Generate tracking report')
    parser.add_argument('--pid', type=int, help='Get summary for specific PID')
    
    args = parser.parse_args()
    
    tracker = ProcessMemoryTracker()
    
    if args.report:
        report = tracker.generate_tracking_report()
        print(json.dumps(report, indent=2))
    elif args.pid:
        summary = tracker.get_process_summary(args.pid)
        if summary:
            print(json.dumps(summary, indent=2))
        else:
            print(f"No data available for PID {args.pid}")
    else:
        try:
            tracker.track_processes(args.duration)
        except KeyboardInterrupt:
            print("\n🛑 Tracking stopped")
        finally:
            # Generate final report
            report = tracker.generate_tracking_report()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = f"memory-monitor/data/tracking_report_{timestamp}.json"
            
            os.makedirs(os.path.dirname(report_file), exist_ok=True)
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"📄 Final report saved to: {report_file}")

if __name__ == "__main__":
    main()