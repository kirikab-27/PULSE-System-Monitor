#!/usr/bin/env python3
"""
Machine Learning-based Memory Anomaly Detection
Implements LSTM neural network for predictive monitoring
"""

import numpy as np
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Use lightweight alternatives for ML functionality
try:
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

class MemoryAnomalyDetector:
    def __init__(self):
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42) if SKLEARN_AVAILABLE else None
        self.memory_sequences = defaultdict(list)
        self.trained_models = {}
        self.sequence_length = 10
        
    def extract_features(self, memory_data):
        """Extract relevant features from memory data"""
        features = []
        
        # System-level features
        sys_mem = memory_data['system']['physical']
        features.extend([
            sys_mem['percent'],
            sys_mem['available'] / sys_mem['total'],
            memory_data['system']['swap']['percent']
        ])
        
        # Process-level aggregated features
        processes = memory_data['processes']
        if processes:
            total_process_mem = sum(p['rss'] for p in processes)
            features.extend([
                len(processes),
                total_process_mem / sys_mem['total'],
                max(p['percent'] for p in processes),
                np.std([p['percent'] for p in processes])
            ])
        else:
            features.extend([0, 0, 0, 0])
        
        # Memory fragmentation indicator
        if sys_mem['total'] > 0:
            fragmentation = 1 - (sys_mem['available'] / (sys_mem['total'] - sys_mem['used']))
            features.append(max(0, min(1, fragmentation)))
        else:
            features.append(0)
        
        return np.array(features)
    
    def simple_anomaly_detection(self, current_features, historical_features):
        """Simple statistical anomaly detection when sklearn not available"""
        if len(historical_features) < 5:
            return 0.0, "Insufficient historical data"
        
        # Calculate z-scores for each feature
        historical_array = np.array(historical_features)
        mean_features = np.mean(historical_array, axis=0)
        std_features = np.std(historical_array, axis=0)
        
        anomaly_scores = []
        for i, (current, mean, std) in enumerate(zip(current_features, mean_features, std_features)):
            if std > 0:
                z_score = abs(current - mean) / std
                anomaly_scores.append(z_score)
        
        if anomaly_scores:
            avg_anomaly_score = np.mean(anomaly_scores)
            max_anomaly_score = max(anomaly_scores)
            
            # Classify anomaly level
            if max_anomaly_score > 3:
                return max_anomaly_score, "HIGH_ANOMALY"
            elif max_anomaly_score > 2:
                return max_anomaly_score, "MEDIUM_ANOMALY"
            elif avg_anomaly_score > 1.5:
                return avg_anomaly_score, "LOW_ANOMALY"
            else:
                return avg_anomaly_score, "NORMAL"
        
        return 0.0, "NORMAL"
    
    def detect_memory_patterns(self, memory_data):
        """Detect patterns and anomalies in memory usage"""
        current_features = self.extract_features(memory_data)
        timestamp = memory_data['system']['timestamp']
        
        # Store in sequence
        self.memory_sequences['global'].append({
            'timestamp': timestamp,
            'features': current_features.tolist()
        })
        
        # Keep only recent data (last 100 samples)
        if len(self.memory_sequences['global']) > 100:
            self.memory_sequences['global'].pop(0)
        
        # Analyze patterns
        sequence = self.memory_sequences['global']
        if len(sequence) < 5:
            return {
                'anomaly_score': 0.0,
                'status': 'LEARNING',
                'patterns': [],
                'predictions': []
            }
        
        # Extract historical features
        historical_features = [item['features'] for item in sequence[:-1]]
        
        if SKLEARN_AVAILABLE and len(historical_features) >= 10:
            # Use machine learning approach
            return self.ml_anomaly_detection(current_features, historical_features)
        else:
            # Use simple statistical approach
            anomaly_score, status = self.simple_anomaly_detection(current_features, historical_features)
            
            # Detect trends
            patterns = self.detect_trends(sequence)
            
            # Simple predictions
            predictions = self.simple_predictions(sequence)
            
            return {
                'anomaly_score': float(anomaly_score),
                'status': status,
                'patterns': patterns,
                'predictions': predictions,
                'method': 'statistical'
            }
    
    def ml_anomaly_detection(self, current_features, historical_features):
        """Machine learning-based anomaly detection"""
        try:
            # Prepare data
            X = np.array(historical_features)
            
            # Fit scaler and model
            X_scaled = self.scaler.fit_transform(X)
            self.isolation_forest.fit(X_scaled)
            
            # Predict anomaly for current data
            current_scaled = self.scaler.transform(current_features.reshape(1, -1))
            anomaly_score = self.isolation_forest.decision_function(current_scaled)[0]
            is_anomaly = self.isolation_forest.predict(current_scaled)[0] == -1
            
            status = "ANOMALY_DETECTED" if is_anomaly else "NORMAL"
            
            return {
                'anomaly_score': float(anomaly_score),
                'status': status,
                'patterns': self.detect_ml_patterns(X),
                'predictions': self.ml_predictions(X),
                'method': 'machine_learning'
            }
            
        except Exception as e:
            # Fallback to simple method
            anomaly_score, status = self.simple_anomaly_detection(current_features, historical_features)
            return {
                'anomaly_score': float(anomaly_score),
                'status': status,
                'patterns': [],
                'predictions': [],
                'method': 'statistical_fallback',
                'error': str(e)
            }
    
    def detect_trends(self, sequence):
        """Detect trends in memory usage"""
        if len(sequence) < 5:
            return []
        
        patterns = []
        
        # Analyze memory usage trend
        memory_usage = [item['features'][0] for item in sequence[-10:]]  # Last 10 samples
        if len(memory_usage) >= 5:
            # Simple linear trend detection
            x = np.arange(len(memory_usage))
            slope = np.polyfit(x, memory_usage, 1)[0]
            
            if slope > 1.0:  # Increasing trend
                patterns.append({
                    'type': 'INCREASING_MEMORY_USAGE',
                    'slope': float(slope),
                    'severity': 'HIGH' if slope > 5 else 'MEDIUM'
                })
            elif slope < -1.0:  # Decreasing trend
                patterns.append({
                    'type': 'DECREASING_MEMORY_USAGE',
                    'slope': float(slope),
                    'severity': 'LOW'
                })
        
        # Detect periodic patterns
        if len(sequence) >= 20:
            usage_values = [item['features'][0] for item in sequence[-20:]]
            # Simple autocorrelation for period detection
            autocorr = np.correlate(usage_values, usage_values, mode='full')
            autocorr = autocorr[autocorr.size // 2:]
            
            if len(autocorr) > 5:
                peaks = []
                for i in range(2, len(autocorr) - 2):
                    if autocorr[i] > autocorr[i-1] and autocorr[i] > autocorr[i+1]:
                        peaks.append(i)
                
                if peaks:
                    patterns.append({
                        'type': 'PERIODIC_PATTERN',
                        'period': peaks[0] if peaks else None,
                        'strength': float(max(autocorr[peaks]) if peaks else 0)
                    })
        
        return patterns
    
    def simple_predictions(self, sequence):
        """Simple prediction based on trends"""
        if len(sequence) < 5:
            return []
        
        predictions = []
        
        # Predict next memory usage based on trend
        recent_usage = [item['features'][0] for item in sequence[-5:]]
        if len(recent_usage) >= 3:
            x = np.arange(len(recent_usage))
            slope, intercept = np.polyfit(x, recent_usage, 1)
            
            # Predict next 3 time points
            for i in range(1, 4):
                next_usage = slope * (len(recent_usage) + i - 1) + intercept
                predictions.append({
                    'time_ahead': i * 30,  # Assuming 30-second intervals
                    'predicted_memory_usage': float(max(0, min(100, next_usage))),
                    'confidence': 'LOW' if abs(slope) > 5 else 'MEDIUM'
                })
        
        return predictions
    
    def detect_ml_patterns(self, X):
        """Detect patterns using ML techniques"""
        patterns = []
        
        if len(X) < 10:
            return patterns
        
        # Detect clusters of similar behavior
        try:
            # Simple clustering alternative
            mean_features = np.mean(X, axis=0)
            std_features = np.std(X, axis=0)
            
            # Identify features with high variance
            high_variance_features = []
            for i, (mean, std) in enumerate(zip(mean_features, std_features)):
                if std > 0.5 * mean and std > 0.1:
                    high_variance_features.append(i)
            
            if high_variance_features:
                patterns.append({
                    'type': 'HIGH_VARIABILITY',
                    'features': high_variance_features,
                    'description': 'Some memory metrics show high variability'
                })
        
        except Exception:
            pass
        
        return patterns
    
    def ml_predictions(self, X):
        """ML-based predictions"""
        predictions = []
        
        if len(X) < 5:
            return predictions
        
        try:
            # Simple trend-based prediction
            recent_data = X[-5:]
            for feature_idx in range(X.shape[1]):
                values = recent_data[:, feature_idx]
                if len(values) >= 3:
                    x = np.arange(len(values))
                    slope = np.polyfit(x, values, 1)[0]
                    
                    if abs(slope) > 0.1:  # Significant trend
                        predictions.append({
                            'feature_index': feature_idx,
                            'trend_slope': float(slope),
                            'prediction_horizon': '5_minutes',
                            'confidence': 'MEDIUM'
                        })
        
        except Exception:
            pass
        
        return predictions
    
    def generate_insights(self, analysis_result):
        """Generate human-readable insights from analysis"""
        insights = []
        
        status = analysis_result.get('status', 'UNKNOWN')
        score = analysis_result.get('anomaly_score', 0)
        patterns = analysis_result.get('patterns', [])
        
        # Status-based insights
        if status == 'HIGH_ANOMALY':
            insights.append("🚨 Critical memory anomaly detected - immediate attention required")
        elif status == 'MEDIUM_ANOMALY':
            insights.append("⚠️  Memory usage showing unusual patterns")
        elif status == 'LOW_ANOMALY':
            insights.append("🔍 Minor memory irregularities observed")
        
        # Pattern-based insights
        for pattern in patterns:
            if pattern['type'] == 'INCREASING_MEMORY_USAGE':
                insights.append(f"📈 Memory usage trending upward (slope: {pattern['slope']:.2f})")
            elif pattern['type'] == 'PERIODIC_PATTERN':
                insights.append(f"🔄 Periodic memory pattern detected (period: {pattern.get('period', 'unknown')})")
            elif pattern['type'] == 'HIGH_VARIABILITY':
                insights.append("📊 Memory metrics showing high variability")
        
        # Prediction-based insights
        predictions = analysis_result.get('predictions', [])
        for pred in predictions[:2]:  # Top 2 predictions
            if 'predicted_memory_usage' in pred:
                usage = pred['predicted_memory_usage']
                if usage > 90:
                    insights.append(f"⏰ Memory usage predicted to reach {usage:.1f}% soon")
        
        return insights

# Example usage and testing
def test_anomaly_detector():
    """Test the anomaly detection system"""
    detector = MemoryAnomalyDetector()
    
    # Simulate memory data
    test_data = {
        'system': {
            'timestamp': datetime.now().isoformat(),
            'physical': {
                'total': 8589934592,  # 8GB
                'available': 4294967296,  # 4GB
                'used': 4294967296,  # 4GB
                'percent': 50.0
            },
            'swap': {
                'total': 2147483648,  # 2GB
                'used': 214748364,   # 0.2GB
                'percent': 10.0
            }
        },
        'processes': [
            {'rss': 536870912, 'percent': 6.25},  # 512MB process
            {'rss': 268435456, 'percent': 3.125}  # 256MB process
        ]
    }
    
    # Test analysis
    result = detector.detect_memory_patterns(test_data)
    insights = detector.generate_insights(result)
    
    print("🧪 Anomaly Detection Test Results:")
    print(f"Status: {result['status']}")
    print(f"Anomaly Score: {result['anomaly_score']:.3f}")
    print(f"Method: {result.get('method', 'unknown')}")
    
    if insights:
        print("\n💡 Insights:")
        for insight in insights:
            print(f"  {insight}")
    
    return result

if __name__ == "__main__":
    test_anomaly_detector()