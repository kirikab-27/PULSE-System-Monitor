#!/usr/bin/env python3
"""
NeuroFlow CPU Monitor - 革新的なリアルタイムCPU監視システム
依存関係なしで動作する軽量版
"""

import json
import time
import os
import sys
from datetime import datetime
from collections import deque
import signal
import subprocess

class NeuroFlowCPUMonitor:
    def __init__(self, history_size=60):
        self.history_size = history_size
        self.cpu_history = deque(maxlen=history_size)
        self.anomaly_threshold = 2.0
        self.running = True
        
    def get_cpu_stats(self):
        """procfsからCPU統計を取得"""
        try:
            with open('/proc/stat', 'r') as f:
                line = f.readline()
            
            cpu_times = [int(x) for x in line.split()[1:]]
            idle = cpu_times[3]
            total = sum(cpu_times)
            return (total - idle), total
        except:
            return 0, 1
    
    def get_cpu_usage(self):
        """CPU使用率を計算（%）"""
        active1, total1 = self.get_cpu_stats()
        time.sleep(0.1)
        active2, total2 = self.get_cpu_stats()
        
        active_diff = active2 - active1
        total_diff = total2 - total1
        
        if total_diff == 0:
            return 0
        
        return (active_diff / total_diff) * 100
    
    def get_per_core_usage(self):
        """コア別CPU使用率を取得"""
        try:
            with open('/proc/stat', 'r') as f:
                lines = f.readlines()
            
            core_stats = []
            for line in lines[1:]:
                if line.startswith('cpu'):
                    cpu_times = [int(x) for x in line.split()[1:]]
                    idle = cpu_times[3]
                    total = sum(cpu_times)
                    core_stats.append((total - idle, total))
                else:
                    break
            
            time.sleep(0.1)
            
            with open('/proc/stat', 'r') as f:
                lines = f.readlines()
            
            core_usages = []
            for i, line in enumerate(lines[1:]):
                if line.startswith('cpu') and i < len(core_stats):
                    cpu_times = [int(x) for x in line.split()[1:]]
                    idle = cpu_times[3]
                    total = sum(cpu_times)
                    
                    active_diff = (total - idle) - core_stats[i][0]
                    total_diff = total - core_stats[i][1]
                    
                    if total_diff == 0:
                        usage = 0
                    else:
                        usage = (active_diff / total_diff) * 100
                    
                    core_usages.append(max(0, min(100, usage)))
                else:
                    break
            
            return core_usages
        except:
            return [0]
    
    def get_load_average(self):
        """ロードアベレージを取得"""
        try:
            with open('/proc/loadavg', 'r') as f:
                loads = f.read().split()[:3]
            return [float(load) for load in loads]
        except:
            return [0.0, 0.0, 0.0]
    
    def get_top_processes(self, limit=10):
        """CPU使用率上位のプロセスを取得"""
        try:
            result = subprocess.run(['ps', 'aux', '--sort=-pcpu'], 
                                  capture_output=True, text=True, timeout=5)
            lines = result.stdout.strip().split('\n')[1:]  # ヘッダーをスキップ
            
            processes = []
            for line in lines[:limit]:
                parts = line.split(None, 10)
                if len(parts) >= 11:
                    try:
                        processes.append({
                            "pid": int(parts[1]),
                            "user": parts[0],
                            "cpu_percent": float(parts[2]),
                            "memory_percent": float(parts[3]),
                            "command": parts[10][:50],  # コマンドを50文字に制限
                            "symphony_note": self._process_to_note(float(parts[2]))
                        })
                    except ValueError:
                        continue
            
            return processes
        except:
            return []
    
    def _process_to_note(self, cpu_percent):
        """CPU使用率を音符に変換（Symphony Visualizer）"""
        notes = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
        octave = min(int(cpu_percent / 20) + 3, 7)
        note_index = int((cpu_percent % 20) / 3)
        return f"{notes[note_index]}{octave}"
    
    def _estimate_temperature(self, usage):
        """使用率から推定温度を計算（相対値）"""
        base_temp = 40
        return base_temp + (usage * 0.4)
    
    def _calculate_health_score(self, usage):
        """CPUコアの健全性スコアを計算"""
        if usage < 70:
            return "excellent"
        elif usage < 85:
            return "good"
        elif usage < 95:
            return "warning"
        else:
            return "critical"
    
    def _analyze_flow_pattern(self, core_usages):
        """ニューロン間の負荷フローパターンを分析"""
        if not core_usages:
            return "unknown"
        
        variance = self._calculate_variance(core_usages)
        
        if variance < 100:
            return "balanced"
        elif variance < 400:
            return "moderate_imbalance"
        else:
            return "high_imbalance"
    
    def _calculate_variance(self, values):
        """分散を計算"""
        if not values:
            return 0
        mean = sum(values) / len(values)
        return sum((x - mean) ** 2 for x in values) / len(values)
    
    def _calculate_standard_deviation(self, values):
        """標準偏差を計算"""
        return self._calculate_variance(values) ** 0.5
    
    def collect_cpu_metrics(self):
        """CPUメトリクスの収集と神経ネットワーク風の表現"""
        overall_usage = self.get_cpu_usage()
        core_usages = self.get_per_core_usage()
        load_avg = self.get_load_average()
        
        # ニューロン（コア）の活性化状態を計算
        neurons = []
        for i, usage in enumerate(core_usages):
            neuron = {
                "core_id": i,
                "activation": usage / 100.0,  # 0-1に正規化
                "temperature": self._estimate_temperature(usage),
                "health_score": self._calculate_health_score(usage)
            }
            neurons.append(neuron)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_usage": overall_usage,
            "neurons": neurons,
            "load_average": load_avg,
            "flow_pattern": self._analyze_flow_pattern(core_usages)
        }
    
    def predict_future_load(self):
        """過去のデータから未来の負荷を予測"""
        if len(self.cpu_history) < 10:
            return None
        
        recent_data = [m['overall_usage'] for m in list(self.cpu_history)[-20:]]
        
        # 簡単なEWMA予測
        alpha = 0.3
        ewma = recent_data[0]
        for value in recent_data[1:]:
            ewma = alpha * value + (1 - alpha) * ewma
        
        # トレンド分析
        recent_avg = sum(recent_data[-5:]) / 5
        older_avg = sum(recent_data[-10:-5]) / 5 if len(recent_data) >= 10 else recent_avg
        
        if recent_avg > older_avg * 1.1:
            trend = "increasing"
        elif recent_avg < older_avg * 0.9:
            trend = "decreasing"
        else:
            trend = "stable"
        
        return {
            "next_5_min": ewma * 1.05,
            "next_15_min": ewma * 1.1,
            "trend": trend,
            "confidence": min(len(recent_data) / 20.0, 1.0)
        }
    
    def detect_anomalies(self):
        """異常検知アルゴリズム"""
        if len(self.cpu_history) < 30:
            return []
        
        recent_usage = [m['overall_usage'] for m in self.cpu_history]
        mean = sum(recent_usage) / len(recent_usage)
        std = self._calculate_standard_deviation(recent_usage)
        current = self.cpu_history[-1]['overall_usage']
        
        z_score = (current - mean) / std if std > 0 else 0
        
        anomalies = []
        if abs(z_score) > self.anomaly_threshold:
            anomalies.append({
                "type": "cpu_spike" if z_score > 0 else "cpu_drop",
                "severity": "high" if abs(z_score) > 3 else "medium",
                "z_score": z_score,
                "recommendation": self._get_recommendation(z_score)
            })
        
        return anomalies
    
    def _get_recommendation(self, z_score):
        """異常に対する推奨アクション"""
        if z_score > 3:
            return "Critical CPU usage detected. Check for runaway processes."
        elif z_score > 2:
            return "High CPU usage. Monitor closely and prepare for scaling."
        elif z_score < -2:
            return "Unusually low CPU usage. Check if services are running correctly."
        else:
            return "Monitor the situation."
    
    def _calculate_overall_health(self):
        """システム全体の健康状態を計算"""
        if not self.cpu_history:
            return "unknown"
        
        recent_usage = self.cpu_history[-1]["overall_usage"]
        if recent_usage < 50:
            return "optimal"
        elif recent_usage < 75:
            return "healthy"
        elif recent_usage < 90:
            return "stressed"
        else:
            return "critical"
    
    def _generate_ascii_visualization(self, metrics):
        """ASCII アートでCPU状態を可視化"""
        neurons = metrics["neurons"]
        viz_lines = []
        
        viz_lines.append("🧠 CPU Neural Network State:")
        viz_lines.append("=" * 50)
        
        for neuron in neurons:
            bar_length = int(neuron["activation"] * 40)
            bar = "█" * bar_length + "░" * (40 - bar_length)
            health_icon = "✓" if neuron["health_score"] in ["excellent", "good"] else "⚠"
            viz_lines.append(f"Core {neuron['core_id']}: [{bar}] {neuron['activation']*100:.1f}% {health_icon}")
        
        return "\n".join(viz_lines)
    
    def generate_beautiful_output(self):
        """美しくフォーマットされた出力を生成"""
        cpu_metrics = self.collect_cpu_metrics()
        self.cpu_history.append(cpu_metrics)
        
        process_metrics = self.get_top_processes()
        prediction = self.predict_future_load()
        anomalies = self.detect_anomalies()
        
        output = {
            "🎯 system_state": {
                "timestamp": cpu_metrics["timestamp"],
                "overall_health": self._calculate_overall_health(),
                "cpu_usage": f"{cpu_metrics['overall_usage']:.1f}%",
                "load_average": cpu_metrics["load_average"],
                "flow_pattern": cpu_metrics["flow_pattern"]
            },
            "🧠 neural_network": {
                "neurons": cpu_metrics["neurons"],
                "total_cores": len(cpu_metrics["neurons"])
            },
            "🎵 process_symphony": {
                "top_performers": process_metrics[:5],
                "total_processes": len(process_metrics)
            },
            "🔮 predictive_insights": prediction,
            "⚠️  anomaly_detection": anomalies,
            "📊 visualization": self._generate_ascii_visualization(cpu_metrics)
        }
        
        return json.dumps(output, indent=2, ensure_ascii=False)
    
    def run_monitoring_loop(self, interval=2):
        """メインモニタリングループ"""
        while self.running:
            try:
                output = self.generate_beautiful_output()
                print("\033[2J\033[H")  # 画面クリア
                print(output)
                time.sleep(interval)
            except KeyboardInterrupt:
                self.stop()
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(interval)
    
    def stop(self):
        """モニタリングを停止"""
        self.running = False
        print("\n🛑 NeuroFlow CPU Monitor stopped.")

def main():
    monitor = NeuroFlowCPUMonitor()
    
    # シグナルハンドラ設定
    def signal_handler(sig, frame):
        monitor.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print("🚀 Starting NeuroFlow CPU Monitor...")
    print("Press Ctrl+C to stop.\n")
    
    # モニタリング開始
    monitor.run_monitoring_loop(interval=2)

if __name__ == "__main__":
    main()