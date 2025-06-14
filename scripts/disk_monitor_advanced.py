#!/usr/bin/env python3
"""
ディスクインテリジェンス・モニター Advanced Edition
AI搭載プロアクティブ監視システム（Python版）
"""

import os
import json
import time
import shutil
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import argparse

class DiskIntelligenceMonitor:
    def __init__(self):
        self.history_dir = os.path.expanduser("~/.disk_monitor_history")
        os.makedirs(self.history_dir, exist_ok=True)
        
    def get_disk_usage(self) -> List[Dict]:
        """ディスク使用量を取得"""
        result = subprocess.run(['df', '-h'], capture_output=True, text=True)
        partitions = []
        
        for line in result.stdout.strip().split('\n')[1:]:
            if line.startswith('/dev/'):
                parts = line.split()
                if len(parts) >= 6:
                    partitions.append({
                        'device': parts[0],
                        'size': parts[1],
                        'used': parts[2],
                        'available': parts[3],
                        'use_percent': int(parts[4].rstrip('%')),
                        'mountpoint': parts[5]
                    })
        return partitions
    
    def predict_capacity_exhaustion(self, device: str, current_usage: int) -> Optional[Dict]:
        """容量枯渇の予測"""
        history_file = os.path.join(
            self.history_dir, 
            f"usage_history_{datetime.now().strftime('%Y%m')}.json"
        )
        
        if not os.path.exists(history_file):
            return None
            
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
        except:
            return None
            
        device_history = [entry for entry in history if entry['device'] == device]
        if len(device_history) < 2:
            return None
            
        # 簡易的な成長率計算
        recent_entries = sorted(device_history, key=lambda x: x['timestamp'])[-5:]
        if len(recent_entries) < 2:
            return None
            
        growth_rate = (recent_entries[-1]['usage'] - recent_entries[0]['usage']) / len(recent_entries)
        
        if growth_rate > 0:
            days_to_full = (100 - current_usage) / growth_rate
            return {
                'days_to_full': days_to_full,
                'growth_rate': growth_rate,
                'risk_level': 'high' if days_to_full < 7 else 'medium' if days_to_full < 30 else 'low'
            }
        
        return None
    
    def save_usage_history(self, partitions: List[Dict]):
        """使用履歴を保存"""
        history_file = os.path.join(
            self.history_dir, 
            f"usage_history_{datetime.now().strftime('%Y%m')}.json"
        )
        
        current_data = {
            'timestamp': datetime.now().isoformat(),
            'data': []
        }
        
        for partition in partitions:
            current_data['data'].append({
                'device': partition['device'],
                'usage': partition['use_percent'],
                'used_space': partition['used'],
                'available_space': partition['available']
            })
        
        # 既存データの読み込み
        history = []
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
            except:
                history = []
        
        # 新しいデータを追加
        for entry in current_data['data']:
            entry['timestamp'] = current_data['timestamp']
            history.append(entry)
        
        # 古いデータを削除（30日以上前）
        cutoff = datetime.now() - timedelta(days=30)
        history = [entry for entry in history if datetime.fromisoformat(entry['timestamp']) > cutoff]
        
        # 保存
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def generate_progress_bar(self, percentage: int, width: int = 50) -> str:
        """プログレスバーを生成"""
        filled = int(percentage * width / 100)
        bar = '█' * filled + '░' * (width - filled)
        
        # 色分け
        if percentage > 90:
            color = '\033[0;31m'  # Red
        elif percentage > 70:
            color = '\033[0;33m'  # Yellow
        else:
            color = '\033[0;32m'  # Green
        
        return f"{color}[{bar}] {percentage}%\033[0m"
    
    def display_3d_visualization(self, partitions: List[Dict]):
        """3Dビジュアライゼーション"""
        print("\033[0;34m▶ 3Dストレージビジュアライゼーション\033[0m")
        print("\033[0;37m" + "━" * 60 + "\033[0m")
        
        print("\033[0;36m     ╱─────────────────────────────╲\033[0m")
        print("\033[0;36m    ╱                               ╲\033[0m")
        
        for partition in partitions:
            height = max(1, partition['use_percent'] // 10)
            
            # 色分け
            if partition['use_percent'] > 80:
                color = '\033[0;31m'  # Red
            elif partition['use_percent'] > 60:
                color = '\033[0;33m'  # Yellow
            else:
                color = '\033[0;32m'  # Green
            
            # 3D柱の描画
            bar = color + '█' * height + '\033[0m' + '░' * (10 - height)
            print(f"   {bar} {partition['mountpoint']:<15} {partition['use_percent']:3d}%")
        
        print("\033[0;36m   ╲_______________________________╱\033[0m")
    
    def check_system_health(self) -> Dict:
        """システム健全性チェック"""
        health_status = {
            'disk_usage': [],
            'large_files': [],
            'inode_usage': [],
            'io_stats': {}
        }
        
        # ディスク使用量チェック
        partitions = self.get_disk_usage()
        for partition in partitions:
            prediction = self.predict_capacity_exhaustion(
                partition['device'], 
                partition['use_percent']
            )
            partition['prediction'] = prediction
            health_status['disk_usage'].append(partition)
        
        # 大きなファイル検出
        try:
            result = subprocess.run(
                ['find', '/', '-xdev', '-type', 'f', '-size', '+100M'], 
                capture_output=True, text=True, timeout=30
            )
            large_files = []
            for file_path in result.stdout.strip().split('\n')[:10]:
                if file_path and os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    large_files.append({
                        'path': file_path,
                        'size_mb': size // (1024 * 1024)
                    })
            health_status['large_files'] = large_files
        except:
            health_status['large_files'] = []
        
        # inode使用状況
        try:
            result = subprocess.run(['df', '-i'], capture_output=True, text=True)
            for line in result.stdout.strip().split('\n')[1:]:
                if line.startswith('/dev/'):
                    parts = line.split()
                    if len(parts) >= 5 and parts[4] != '-':
                        health_status['inode_usage'].append({
                            'device': parts[0],
                            'inode_usage': int(parts[4].rstrip('%')),
                            'mountpoint': parts[5] if len(parts) > 5 else 'unknown'
                        })
        except:
            pass
        
        return health_status
    
    def display_health_report(self, health_status: Dict):
        """健全性レポート表示"""
        print("\033[0;34m▶ システム健全性レポート\033[0m")
        print("\033[0;37m" + "━" * 60 + "\033[0m")
        
        # ディスク使用量と予測
        print("\033[0;36mディスク使用状況と予測:\033[0m")
        for partition in health_status['disk_usage']:
            device_name = partition['device'].split('/')[-1]
            print(f"  {device_name:<15} {partition['mountpoint']:<20}")
            print(f"    {self.generate_progress_bar(partition['use_percent'])}")
            print(f"    容量: {partition['size']} | 使用: {partition['used']} | 空き: {partition['available']}")
            
            if partition['prediction']:
                pred = partition['prediction']
                if pred['risk_level'] == 'high':
                    print(f"    \033[0;31m⚠ 警告: 約{pred['days_to_full']:.1f}日で容量不足の可能性\033[0m")
                elif pred['risk_level'] == 'medium':
                    print(f"    \033[0;33m📊 予測: 約{pred['days_to_full']:.1f}日で満杯になる可能性\033[0m")
            print()
        
        # 大きなファイル
        if health_status['large_files']:
            print("\033[0;36m大容量ファイル (上位10件):\033[0m")
            for file_info in health_status['large_files'][:10]:
                print(f"  \033[0;33m{file_info['size_mb']:4d}MB\033[0m - {file_info['path']}")
            print()
        
        # inode使用状況
        if health_status['inode_usage']:
            print("\033[0;36minode使用状況:\033[0m")
            for inode_info in health_status['inode_usage']:
                usage = inode_info['inode_usage']
                color = '\033[0;31m' if usage > 80 else '\033[0;33m' if usage > 60 else '\033[0;32m'
                print(f"  {inode_info['device']:<20} {color}{usage:3d}%\033[0m - {inode_info['mountpoint']}")
            print()
    
    def run_monitoring(self, interval: int = 5):
        """監視実行"""
        try:
            while True:
                os.system('clear')
                
                # ヘッダー表示
                print("\033[0;36m" + "╔" + "═" * 62 + "╗\033[0m")
                print("\033[0;36m║\033[0;37m        ディスクインテリジェンス・モニター Advanced v1.0        \033[0;36m║\033[0m")
                print("\033[0;36m║\033[0;37m        AI搭載プロアクティブ監視システム (Python版)              \033[0;36m║\033[0m")
                print("\033[0;36m" + "╚" + "═" * 62 + "╝\033[0m")
                print()
                
                # パーティション情報取得
                partitions = self.get_disk_usage()
                self.save_usage_history(partitions)
                
                # 健全性チェック
                health_status = self.check_system_health()
                
                # 結果表示
                self.display_health_report(health_status)
                self.display_3d_visualization(partitions)
                
                print(f"\n\033[0;35m最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\033[0m")
                print(f"\033[0;37m次回更新まで {interval} 秒... (Ctrl+C で終了)\033[0m")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\033[0;32m監視を終了します。\033[0m")

def main():
    parser = argparse.ArgumentParser(description='ディスクインテリジェンス・モニター Advanced Edition')
    parser.add_argument('-i', '--interval', type=int, default=5, help='更新間隔（秒）')
    parser.add_argument('--once', action='store_true', help='一回だけ実行')
    
    args = parser.parse_args()
    
    monitor = DiskIntelligenceMonitor()
    
    if args.once:
        # 一回だけ実行
        os.system('clear')
        partitions = monitor.get_disk_usage()
        monitor.save_usage_history(partitions)
        health_status = monitor.check_system_health()
        monitor.display_health_report(health_status)
        monitor.display_3d_visualization(partitions)
    else:
        # 継続監視
        monitor.run_monitoring(args.interval)

if __name__ == "__main__":
    main()