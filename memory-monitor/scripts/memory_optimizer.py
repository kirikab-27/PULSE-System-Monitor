#!/usr/bin/env python3
"""
Intelligent Memory Optimization Engine
Provides automated memory optimization suggestions and actions
"""

import os
import psutil
import json
import subprocess
import time
from datetime import datetime
from collections import defaultdict
import threading

class MemoryOptimizer:
    def __init__(self):
        self.optimization_history = []
        self.system_profile = None
        self.running_optimizations = []
        
    def analyze_system_profile(self):
        """Analyze system characteristics for optimization"""
        system_info = {
            'total_memory': psutil.virtual_memory().total,
            'cpu_count': psutil.cpu_count(),
            'boot_time': psutil.boot_time(),
            'platform': os.name,
            'swap_available': psutil.swap_memory().total > 0
        }
        
        # Categorize system size
        total_gb = system_info['total_memory'] / (1024**3)
        if total_gb < 4:
            system_info['category'] = 'low_memory'
        elif total_gb < 16:
            system_info['category'] = 'medium_memory'
        else:
            system_info['category'] = 'high_memory'
        
        self.system_profile = system_info
        return system_info
    
    def analyze_memory_usage_patterns(self):
        """Analyze current memory usage patterns"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Get process information
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'memory_percent', 'cpu_percent']):
            try:
                pinfo = proc.info
                processes.append({
                    'pid': pinfo['pid'],
                    'name': pinfo['name'],
                    'rss': pinfo['memory_info'].rss,
                    'vms': pinfo['memory_info'].vms,
                    'memory_percent': pinfo['memory_percent'],
                    'cpu_percent': pinfo['cpu_percent']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by memory usage
        processes.sort(key=lambda x: x['rss'], reverse=True)
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'system_memory': {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percent': memory.percent,
                'buffers': getattr(memory, 'buffers', 0),
                'cached': getattr(memory, 'cached', 0)
            },
            'swap_memory': {
                'total': swap.total,
                'used': swap.used,
                'percent': swap.percent
            },
            'top_processes': processes[:20],
            'process_count': len(processes),
            'memory_distribution': self.calculate_memory_distribution(processes)
        }
        
        return analysis
    
    def calculate_memory_distribution(self, processes):
        """Calculate how memory is distributed among processes"""
        total_process_memory = sum(p['rss'] for p in processes)
        
        # Categorize processes by memory usage
        categories = {
            'high_memory': [],  # >100MB
            'medium_memory': [],  # 10-100MB
            'low_memory': []   # <10MB
        }
        
        for proc in processes:
            rss_mb = proc['rss'] / (1024 * 1024)
            if rss_mb > 100:
                categories['high_memory'].append(proc)
            elif rss_mb > 10:
                categories['medium_memory'].append(proc)
            else:
                categories['low_memory'].append(proc)
        
        return {
            'total_process_memory': total_process_memory,
            'high_memory_count': len(categories['high_memory']),
            'medium_memory_count': len(categories['medium_memory']),
            'low_memory_count': len(categories['low_memory']),
            'memory_concentration': len(categories['high_memory']) / len(processes) if processes else 0
        }
    
    def generate_optimization_strategies(self, analysis):
        """Generate specific optimization strategies"""
        strategies = []
        system_mem = analysis['system_memory']
        swap_mem = analysis['swap_memory']
        top_processes = analysis['top_processes']
        
        # Strategy 1: High memory usage mitigation
        if system_mem['percent'] > 85:
            strategies.append({
                'type': 'CRITICAL_MEMORY_PRESSURE',
                'priority': 'HIGH',
                'title': 'Critical Memory Pressure Relief',
                'description': f"System memory usage at {system_mem['percent']:.1f}%",
                'actions': [
                    'identify_memory_hogs',
                    'clear_system_caches',
                    'restart_heavy_processes',
                    'enable_swap_optimization'
                ],
                'estimated_impact': 'High',
                'risk_level': 'Medium'
            })
        
        # Strategy 2: Process optimization
        memory_hogs = [p for p in top_processes if p['memory_percent'] > 10]
        if memory_hogs:
            strategies.append({
                'type': 'PROCESS_OPTIMIZATION',
                'priority': 'MEDIUM',
                'title': 'Optimize High-Memory Processes',
                'description': f"Found {len(memory_hogs)} processes consuming >10% memory",
                'processes': [{'name': p['name'], 'pid': p['pid'], 'memory_percent': p['memory_percent']} for p in memory_hogs[:5]],
                'actions': [
                    'analyze_process_behavior',
                    'suggest_process_limits',
                    'recommend_alternatives'
                ],
                'estimated_impact': 'Medium',
                'risk_level': 'Low'
            })
        
        # Strategy 3: Cache optimization
        cache_size = system_mem.get('cached', 0)
        if cache_size > system_mem['total'] * 0.3:  # Cache using >30% of total memory
            strategies.append({
                'type': 'CACHE_OPTIMIZATION',
                'priority': 'LOW',
                'title': 'Optimize System Cache Usage',
                'description': f"System cache using {cache_size / system_mem['total'] * 100:.1f}% of total memory",
                'actions': [
                    'tune_cache_parameters',
                    'clear_stale_caches',
                    'optimize_cache_policy'
                ],
                'estimated_impact': 'Low',
                'risk_level': 'Very Low'
            })
        
        # Strategy 4: Swap optimization
        if swap_mem['total'] > 0 and swap_mem['percent'] > 20:
            strategies.append({
                'type': 'SWAP_OPTIMIZATION',
                'priority': 'MEDIUM',
                'title': 'Optimize Swap Usage',
                'description': f"Swap usage at {swap_mem['percent']:.1f}%",
                'actions': [
                    'adjust_swappiness',
                    'optimize_swap_priority',
                    'consider_swap_alternatives'
                ],
                'estimated_impact': 'Medium',
                'risk_level': 'Low'
            })
        
        # Strategy 5: System-specific optimizations
        if self.system_profile:
            if self.system_profile['category'] == 'low_memory':
                strategies.append({
                    'type': 'LOW_MEMORY_SYSTEM',
                    'priority': 'HIGH',
                    'title': 'Low Memory System Optimization',
                    'description': 'Optimize for memory-constrained environment',
                    'actions': [
                        'disable_unnecessary_services',
                        'optimize_kernel_parameters',
                        'use_lightweight_alternatives'
                    ],
                    'estimated_impact': 'High',
                    'risk_level': 'Medium'
                })
        
        return strategies
    
    def execute_safe_optimizations(self, strategies):
        """Execute safe, non-destructive optimizations"""
        results = []
        
        for strategy in strategies:
            if strategy['risk_level'] in ['Very Low', 'Low']:
                try:
                    result = self._execute_strategy(strategy)
                    results.append(result)
                except Exception as e:
                    results.append({
                        'strategy': strategy['title'],
                        'status': 'failed',
                        'error': str(e)
                    })
        
        return results
    
    def _execute_strategy(self, strategy):
        """Execute a specific optimization strategy"""
        strategy_type = strategy['type']
        
        if strategy_type == 'CACHE_OPTIMIZATION':
            return self._optimize_cache()
        elif strategy_type == 'SWAP_OPTIMIZATION':
            return self._optimize_swap()
        elif strategy_type == 'PROCESS_OPTIMIZATION':
            return self._analyze_processes(strategy)
        else:
            return {
                'strategy': strategy['title'],
                'status': 'skipped',
                'reason': 'Strategy execution not implemented'
            }
    
    def _optimize_cache(self):
        """Optimize system cache (safe operations only)"""
        results = {'strategy': 'Cache Optimization', 'actions': []}
        
        try:
            # Get cache information
            if hasattr(psutil, 'virtual_memory'):
                memory = psutil.virtual_memory()
                cached = getattr(memory, 'cached', 0)
                
                results['actions'].append({
                    'action': 'analyze_cache',
                    'current_cache_size': cached,
                    'cache_percentage': cached / memory.total * 100,
                    'recommendation': 'Monitor cache usage patterns'
                })
            
            # Check for obvious cache-heavy processes
            cache_heavy_processes = []
            for proc in psutil.process_iter(['name', 'memory_info']):
                try:
                    if proc.info['memory_info'].rss > 100 * 1024 * 1024:  # >100MB
                        name = proc.info['name'].lower()
                        if any(keyword in name for keyword in ['cache', 'browser', 'chrome', 'firefox']):
                            cache_heavy_processes.append(proc.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if cache_heavy_processes:
                results['actions'].append({
                    'action': 'identify_cache_heavy_processes',
                    'processes': cache_heavy_processes[:5],
                    'recommendation': 'Consider restarting these processes if memory is needed'
                })
            
            results['status'] = 'completed'
            
        except Exception as e:
            results['status'] = 'failed'
            results['error'] = str(e)
        
        return results
    
    def _optimize_swap(self):
        """Optimize swap usage (analysis and recommendations)"""
        results = {'strategy': 'Swap Optimization', 'actions': []}
        
        try:
            swap = psutil.swap_memory()
            
            results['actions'].append({
                'action': 'analyze_swap',
                'current_swap_usage': swap.used,
                'swap_percentage': swap.percent,
                'total_swap': swap.total
            })
            
            # Check swappiness value (Linux only)
            if os.name == 'posix':
                try:
                    with open('/proc/sys/vm/swappiness', 'r') as f:
                        swappiness = int(f.read().strip())
                    
                    recommendation = ""
                    if swappiness > 60:
                        recommendation = "Consider reducing swappiness for better performance"
                    elif swappiness < 10:
                        recommendation = "Swappiness is very low, may cause memory pressure"
                    else:
                        recommendation = "Swappiness value appears optimal"
                    
                    results['actions'].append({
                        'action': 'check_swappiness',
                        'current_value': swappiness,
                        'recommendation': recommendation
                    })
                
                except (FileNotFoundError, PermissionError):
                    results['actions'].append({
                        'action': 'check_swappiness',
                        'status': 'unavailable',
                        'reason': 'Cannot access swappiness parameter'
                    })
            
            results['status'] = 'completed'
            
        except Exception as e:
            results['status'] = 'failed'
            results['error'] = str(e)
        
        return results
    
    def _analyze_processes(self, strategy):
        """Analyze processes for optimization opportunities"""
        results = {'strategy': 'Process Analysis', 'actions': []}
        
        try:
            processes = strategy.get('processes', [])
            
            for proc_info in processes:
                try:
                    proc = psutil.Process(proc_info['pid'])
                    
                    # Get additional process information
                    connections = len([conn for conn in proc.connections() if conn.status == psutil.CONN_ESTABLISHED])
                    num_threads = proc.num_threads()
                    
                    analysis = {
                        'pid': proc_info['pid'],
                        'name': proc_info['name'],
                        'memory_percent': proc_info['memory_percent'],
                        'connections': connections,
                        'threads': num_threads,
                        'recommendations': []
                    }
                    
                    # Generate recommendations
                    if proc_info['memory_percent'] > 15:
                        analysis['recommendations'].append("High memory usage - monitor for memory leaks")
                    
                    if num_threads > 50:
                        analysis['recommendations'].append("High thread count - may benefit from optimization")
                    
                    if connections > 100:
                        analysis['recommendations'].append("Many network connections - check if necessary")
                    
                    results['actions'].append(analysis)
                
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    results['actions'].append({
                        'pid': proc_info['pid'],
                        'name': proc_info['name'],
                        'status': 'process_not_available'
                    })
            
            results['status'] = 'completed'
            
        except Exception as e:
            results['status'] = 'failed'
            results['error'] = str(e)
        
        return results
    
    def generate_optimization_report(self):
        """Generate comprehensive optimization report"""
        # Analyze current system
        system_profile = self.analyze_system_profile()
        memory_analysis = self.analyze_memory_usage_patterns()
        strategies = self.generate_optimization_strategies(memory_analysis)
        
        # Execute safe optimizations
        optimization_results = self.execute_safe_optimizations(strategies)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'system_profile': system_profile,
            'memory_analysis': memory_analysis,
            'optimization_strategies': strategies,
            'executed_optimizations': optimization_results,
            'summary': {
                'total_strategies': len(strategies),
                'executed_optimizations': len(optimization_results),
                'memory_usage_percent': memory_analysis['system_memory']['percent'],
                'top_memory_consumer': memory_analysis['top_processes'][0]['name'] if memory_analysis['top_processes'] else 'N/A'
            }
        }
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"memory-monitor/data/optimization_report_{timestamp}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report, report_file
    
    def get_quick_optimization_tips(self):
        """Get quick optimization tips based on current state"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        tips = []
        
        if memory.percent > 80:
            tips.append("💡 High memory usage detected - consider closing unused applications")
        
        if swap.percent > 30:
            tips.append("💡 High swap usage - system may benefit from more RAM")
        
        # Check for obvious memory-hungry processes
        top_processes = []
        for proc in psutil.process_iter(['name', 'memory_percent']):
            try:
                if proc.info['memory_percent'] > 5:
                    top_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if top_processes:
            top_process = max(top_processes, key=lambda x: x['memory_percent'])
            tips.append(f"💡 '{top_process['name']}' is using {top_process['memory_percent']:.1f}% of memory")
        
        if len(tips) == 0:
            tips.append("✅ Memory usage appears to be in good shape")
        
        return tips

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Memory Optimization Engine')
    parser.add_argument('--report', action='store_true', help='Generate full optimization report')
    parser.add_argument('--tips', action='store_true', help='Show quick optimization tips')
    parser.add_argument('--analyze', action='store_true', help='Analyze current memory state')
    
    args = parser.parse_args()
    
    optimizer = MemoryOptimizer()
    
    if args.tips:
        tips = optimizer.get_quick_optimization_tips()
        print("🔧 Quick Optimization Tips:")
        for tip in tips:
            print(f"   {tip}")
    
    elif args.analyze:
        analysis = optimizer.analyze_memory_usage_patterns()
        print(f"📊 Memory Analysis at {analysis['timestamp']}")
        print(f"System Memory: {analysis['system_memory']['percent']:.1f}% used")
        print(f"Swap Memory: {analysis['swap_memory']['percent']:.1f}% used")
        print(f"Total Processes: {analysis['process_count']}")
        
        if analysis['top_processes']:
            print(f"\nTop Memory Consumers:")
            for i, proc in enumerate(analysis['top_processes'][:5], 1):
                print(f"  {i}. {proc['name']} - {proc['memory_percent']:.1f}%")
    
    elif args.report:
        print("🚀 Generating comprehensive optimization report...")
        report, report_file = optimizer.generate_optimization_report()
        
        print(f"📄 Report saved to: {report_file}")
        print(f"📊 Summary:")
        print(f"   Memory Usage: {report['summary']['memory_usage_percent']:.1f}%")
        print(f"   Optimization Strategies: {report['summary']['total_strategies']}")
        print(f"   Executed Optimizations: {report['summary']['executed_optimizations']}")
        print(f"   Top Memory Consumer: {report['summary']['top_memory_consumer']}")
    
    else:
        # Default: show tips
        tips = optimizer.get_quick_optimization_tips()
        print("🔧 Memory Optimization Tips:")
        for tip in tips:
            print(f"   {tip}")
        print("\nUse --report for detailed analysis or --help for more options")

if __name__ == "__main__":
    main()