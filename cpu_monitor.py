#!/usr/bin/env python3
"""
NeuroFlow CPU Monitor - 革新的なリアルタイムCPU監視システム
神経ネットワークにインスパイアされた動的な監視と予測分析を提供
"""

import psutil
import json
import time
import os
import sys
from datetime import datetime
from collections import deque
import numpy as np
from threading import Thread
import signal


class NeuroFlowCPUMonitor:
    def __init__(self, history_size=60):
        self.history_size = history_size
        self.cpu_history = deque(maxlen=history_size)
        self.process_history = {}
        self.anomaly_threshold = 2.0  # 標準偏差の倍数
        self.running = True
        self.prediction_model = PredictiveModel()
        
    def collect_cpu_metrics(self):
        """CPUメトリクスの収集と神経ネットワーク風の表現"""
        cpu_percent_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
        cpu_freq = psutil.cpu_freq()
        cpu_stats = psutil.cpu_stats()
        
        # ニューロン（コア）の活性化状態を計算
        neurons = []
        for i, usage in enumerate(cpu_percent_per_core):
            neuron = {
                "core_id": i,
                "activation": usage / 100.0,  # 0-1に正規化
                "frequency": cpu_freq.current if cpu_freq else 0,
                "temperature": self._estimate_temperature(usage),
                "health_score": self._calculate_health_score(usage)
            }
            neurons.append(neuron)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_usage": psutil.cpu_percent(interval=0),
            "neurons": neurons,
            "context_switches": cpu_stats.ctx_switches,
            "interrupts": cpu_stats.interrupts,
            "load_average": os.getloadavg(),
            "flow_pattern": self._analyze_flow_pattern(neurons)
        }
    
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
    
    def _analyze_flow_pattern(self, neurons):
        """ニューロン間の負荷フローパターンを分析"""
        activations = [n["activation"] for n in neurons]
        variance = np.var(activations)
        
        if variance < 0.1:
            return "balanced"
        elif variance < 0.3:
            return "moderate_imbalance"
        else:
            return "high_imbalance"
    
    def collect_process_metrics(self, top_n=10):
        """プロセス別の詳細メトリクス収集"""
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                if pinfo['cpu_percent'] > 0:
                    processes.append({
                        "pid": pinfo['pid'],
                        "name": pinfo['name'],
                        "cpu_percent": pinfo['cpu_percent'],
                        "memory_percent": pinfo['memory_percent'],
                        "priority": proc.nice(),
                        "threads": proc.num_threads(),
                        "symphony_note": self._process_to_note(pinfo['cpu_percent'])
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # CPU使用率でソートして上位N個を返す
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        return processes[:top_n]
    
    def _process_to_note(self, cpu_percent):
        """CPU使用率を音符に変換（Symphony Visualizer）"""
        notes = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
        octave = min(int(cpu_percent / 20) + 3, 7)
        note_index = int((cpu_percent % 20) / 3)
        return f"{notes[note_index]}{octave}"
    
    def predict_future_load(self):
        """過去のデータから未来の負荷を予測"""
        if len(self.cpu_history) < 10:
            return None
        
        recent_data = [m['overall_usage'] for m in list(self.cpu_history)[-20:]]
        prediction = self.prediction_model.predict(recent_data)
        
        return {
            "next_5_min": prediction['short_term'],
            "next_15_min": prediction['medium_term'],
            "trend": prediction['trend'],
            "anomaly_probability": prediction['anomaly_prob']
        }
    
    def detect_anomalies(self):
        """異常検知アルゴリズム"""
        if len(self.cpu_history) < 30:
            return None
        
        recent_usage = [m['overall_usage'] for m in self.cpu_history]
        mean = np.mean(recent_usage)
        std = np.std(recent_usage)
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
        
        # 負荷パターンの異常検知
        flow_pattern = self.cpu_history[-1]['neurons']
        imbalance_score = self._calculate_imbalance_score(flow_pattern)
        if imbalance_score > 0.7:
            anomalies.append({
                "type": "load_imbalance",
                "severity": "medium",
                "imbalance_score": imbalance_score,
                "recommendation": "Consider load balancing or process affinity adjustments"
            })
        
        return anomalies
    
    def _calculate_imbalance_score(self, neurons):
        """負荷の不均衡スコアを計算"""
        activations = [n["activation"] for n in neurons]
        return np.std(activations) / (np.mean(activations) + 0.01)
    
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
    
    def generate_beautiful_output(self):
        """美しくフォーマットされた出力を生成"""
        cpu_metrics = self.collect_cpu_metrics()
        self.cpu_history.append(cpu_metrics)
        
        process_metrics = self.collect_process_metrics()
        prediction = self.predict_future_load()
        anomalies = self.detect_anomalies()
        
        output = {
            "system_state": {
                "timestamp": cpu_metrics["timestamp"],
                "overall_health": self._calculate_overall_health(),
                "cpu_usage": cpu_metrics["overall_usage"],
                "load_average": cpu_metrics["load_average"],
                "flow_pattern": cpu_metrics["flow_pattern"]
            },
            "neural_network": {
                "neurons": cpu_metrics["neurons"],
                "connections": self._calculate_neuron_connections(cpu_metrics["neurons"])
            },
            "process_symphony": {
                "top_performers": process_metrics,
                "harmony_score": self._calculate_harmony_score(process_metrics)
            },
            "predictive_insights": prediction,
            "anomaly_detection": anomalies,
            "visualization": self._generate_ascii_visualization(cpu_metrics)
        }
        
        return json.dumps(output, indent=2)
    
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
    
    def _calculate_neuron_connections(self, neurons):
        """ニューロン間の接続強度を計算"""
        connections = []
        for i in range(len(neurons)):
            for j in range(i + 1, len(neurons)):
                strength = abs(neurons[i]["activation"] - neurons[j]["activation"])
                connections.append({
                    "from": i,
                    "to": j,
                    "strength": 1 - strength  # 類似性が高いほど強い接続
                })
        return connections
    
    def _calculate_harmony_score(self, processes):
        """プロセス群の調和スコアを計算"""
        if not processes:
            return 1.0
        
        cpu_usages = [p["cpu_percent"] for p in processes]
        variance = np.var(cpu_usages)
        
        # 分散が小さいほど調和的
        return max(0, 1 - (variance / 1000))
    
    def _generate_ascii_visualization(self, metrics):
        """ASCIIアートでCPU状態を可視化"""
        neurons = metrics["neurons"]
        viz_lines = []
        
        viz_lines.append("CPU Neural Network State:")
        viz_lines.append("=" * 50)
        
        for neuron in neurons:
            bar_length = int(neuron["activation"] * 40)
            bar = "█" * bar_length + "░" * (40 - bar_length)
            health_icon = "✓" if neuron["health_score"] in ["excellent", "good"] else "!"
            viz_lines.append(f"Core {neuron['core_id']}: [{bar}] {neuron['activation']*100:.1f}% {health_icon}")
        
        return "\n".join(viz_lines)
    
    def run_monitoring_loop(self, interval=1):
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
        print("\nNeuroFlow CPU Monitor stopped.")


class PredictiveModel:
    """簡単な予測モデル（EWMA）"""
    
    def __init__(self, alpha=0.3):
        self.alpha = alpha
    
    def predict(self, data):
        """指数加重移動平均による予測"""
        if len(data) < 2:
            return {
                "short_term": data[-1] if data else 0,
                "medium_term": data[-1] if data else 0,
                "trend": "stable",
                "anomaly_prob": 0
            }
        
        # EWMA計算
        ewma = data[0]
        for value in data[1:]:
            ewma = self.alpha * value + (1 - self.alpha) * ewma
        
        # トレンド分析
        recent_avg = np.mean(data[-5:])
        older_avg = np.mean(data[-10:-5]) if len(data) >= 10 else recent_avg
        
        if recent_avg > older_avg * 1.1:
            trend = "increasing"
        elif recent_avg < older_avg * 0.9:
            trend = "decreasing"
        else:
            trend = "stable"
        
        # 異常確率
        std_dev = np.std(data)
        current_deviation = abs(data[-1] - ewma)
        anomaly_prob = min(current_deviation / (std_dev + 0.1), 1.0)
        
        return {
            "short_term": ewma * 1.05,  # 5%の余裕を持たせる
            "medium_term": ewma * 1.1,   # 10%の余裕を持たせる
            "trend": trend,
            "anomaly_prob": anomaly_prob
        }


def main():
    monitor = NeuroFlowCPUMonitor()
    
    # シグナルハンドラ設定
    def signal_handler(sig, frame):
        monitor.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print("Starting NeuroFlow CPU Monitor...")
    print("Press Ctrl+C to stop.\n")
    
    # モニタリング開始
    monitor.run_monitoring_loop(interval=2)


if __name__ == "__main__":
    main()