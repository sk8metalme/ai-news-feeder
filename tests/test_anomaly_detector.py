"""anomaly_detector.pyのテスト"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, timedelta
from src.utils.anomaly_detector import AnomalyDetector, ExecutionResult, Alert


class TestAnomalyDetector:
    """AnomalyDetectorクラスのテスト"""
    
    @pytest.fixture
    def detector(self):
        """AnomalyDetectorインスタンスを返す"""
        with patch('src.utils.anomaly_detector.AnomalyDetector._load_history'):
            detector = AnomalyDetector()
            detector.execution_history.clear()
            detector.alert_history = []
            return detector
    
    @pytest.fixture
    def success_result(self):
        """成功した実行結果"""
        return ExecutionResult(
            timestamp=datetime.now(),
            success=True,
            articles_found=10,
            articles_verified=5,
            processing_time_seconds=60.0,
            error_message=None
        )
    
    @pytest.fixture
    def failure_result(self):
        """失敗した実行結果"""
        return ExecutionResult(
            timestamp=datetime.now(),
            success=False,
            articles_found=0,
            articles_verified=0,
            processing_time_seconds=10.0,
            error_message="API Error"
        )
    
    def test_record_execution_success(self, detector, success_result):
        """成功実行の記録テスト"""
        with patch.object(detector, '_save_history'):
            with patch.object(detector, '_detect_anomalies', return_value=[]):
                detector.record_execution(success_result)
        
        assert len(detector.execution_history) == 1
        assert detector.execution_history[0]['success'] is True
        assert detector.execution_history[0]['articles_found'] == 10
    
    def test_consecutive_failures_detection(self, detector, failure_result):
        """連続失敗検知のテスト"""
        # 3回連続で失敗を記録
        for i in range(3):
            detector.execution_history.append({
                'timestamp': failure_result.timestamp.isoformat(),
                'success': False,
                'articles_found': 0,
                'articles_verified': 0,
                'processing_time_seconds': 10.0,
                'error_message': f"Error {i+1}"
            })
        
        alert = detector._check_consecutive_failures()
        
        assert alert is not None
        assert alert.type == "consecutive_failures"
        assert alert.severity == "critical"
        assert "3回連続" in alert.message
    
    def test_no_consecutive_failures(self, detector, success_result, failure_result):
        """連続失敗なしの場合のテスト"""
        # 成功と失敗を交互に記録
        detector.execution_history.append({
            'timestamp': failure_result.timestamp.isoformat(),
            'success': False,
            'articles_found': 0,
            'articles_verified': 0,
            'processing_time_seconds': 10.0,
            'error_message': "Error 1"
        })
        detector.execution_history.append({
            'timestamp': success_result.timestamp.isoformat(),
            'success': True,
            'articles_found': 10,
            'articles_verified': 5,
            'processing_time_seconds': 60.0,
            'error_message': None
        })
        detector.execution_history.append({
            'timestamp': failure_result.timestamp.isoformat(),
            'success': False,
            'articles_found': 0,
            'articles_verified': 0,
            'processing_time_seconds': 10.0,
            'error_message': "Error 2"
        })
        
        alert = detector._check_consecutive_failures()
        assert alert is None
    
    def test_low_article_count_critical(self, detector):
        """記事数不足（クリティカル）のテスト"""
        result = ExecutionResult(
            timestamp=datetime.now(),
            success=True,
            articles_found=5,
            articles_verified=0,  # 0件でクリティカル
            processing_time_seconds=60.0
        )
        
        alert = detector._check_article_count(result)
        
        assert alert is not None
        assert alert.type == "low_articles"
        assert alert.severity == "critical"
        assert "0件" in alert.message
    
    def test_low_article_count_warning(self, detector):
        """記事数不足（警告）のテスト"""
        result = ExecutionResult(
            timestamp=datetime.now(),
            success=True,
            articles_found=10,
            articles_verified=2,  # 少ないが0ではない
            processing_time_seconds=60.0
        )
        
        alert = detector._check_article_count(result)
        
        assert alert is not None
        assert alert.type == "low_articles"
        assert alert.severity == "warning"
        assert "少なくなっています" in alert.message
    
    def test_article_count_normal(self, detector):
        """記事数正常の場合のテスト"""
        result = ExecutionResult(
            timestamp=datetime.now(),
            success=True,
            articles_found=10,
            articles_verified=5,
            processing_time_seconds=60.0
        )
        
        alert = detector._check_article_count(result)
        assert alert is None
    
    def test_performance_degradation_critical(self, detector):
        """パフォーマンス劣化（クリティカル）のテスト"""
        # ベースラインを設定
        detector.baseline_performance = {
            'avg_processing_time': 60.0,
            'avg_articles_verified': 5.0,
            'sample_size': 10
        }
        
        # 3倍以上遅い
        result = ExecutionResult(
            timestamp=datetime.now(),
            success=True,
            articles_found=10,
            articles_verified=5,
            processing_time_seconds=200.0
        )
        
        alert = detector._check_performance(result)
        
        assert alert is not None
        assert alert.type == "performance_degradation"
        assert alert.severity == "critical"
        assert "異常に長く" in alert.message
    
    def test_performance_degradation_warning(self, detector):
        """パフォーマンス劣化（警告）のテスト"""
        detector.baseline_performance = {
            'avg_processing_time': 60.0,
            'avg_articles_verified': 5.0,
            'sample_size': 10
        }
        
        # 2倍程度遅い
        result = ExecutionResult(
            timestamp=datetime.now(),
            success=True,
            articles_found=10,
            articles_verified=5,
            processing_time_seconds=130.0
        )
        
        alert = detector._check_performance(result)
        
        assert alert is not None
        assert alert.type == "performance_degradation"
        assert alert.severity == "warning"
        assert "増加しています" in alert.message
    
    def test_performance_normal(self, detector):
        """パフォーマンス正常の場合のテスト"""
        detector.baseline_performance = {
            'avg_processing_time': 60.0,
            'avg_articles_verified': 5.0,
            'sample_size': 10
        }
        
        result = ExecutionResult(
            timestamp=datetime.now(),
            success=True,
            articles_found=10,
            articles_verified=5,
            processing_time_seconds=65.0  # わずかに遅い程度
        )
        
        alert = detector._check_performance(result)
        assert alert is None
    
    @patch('src.utils.slack_notifier.SlackNotifier.session')
    def test_send_alert(self, mock_session, detector):
        """アラート送信のテスト"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.post.return_value = mock_response
        
        alert = Alert(
            type="consecutive_failures",
            severity="critical",
            message="テストアラート",
            details={'test': True},
            timestamp=datetime.now()
        )
        
        detector._send_alert(alert)
        
        assert mock_session.post.called
        assert len(detector.alert_history) == 1
    
    def test_duplicate_alert_prevention(self, detector):
        """重複アラート防止のテスト"""
        # 既存のアラートを追加
        detector.alert_history.append({
            'type': 'consecutive_failures',
            'severity': 'critical',
            'message': 'Test',
            'details': {},
            'timestamp': datetime.now().isoformat()
        })
        
        # 同じタイプのアラート
        alert = Alert(
            type="consecutive_failures",
            severity="critical",
            message="新しいメッセージ",
            details={},
            timestamp=datetime.now()
        )
        
        is_duplicate = detector._is_duplicate_alert(alert)
        assert is_duplicate is True
    
    def test_calculate_baseline(self, detector):
        """ベースライン計算のテスト"""
        # 10件の成功実行を追加
        for i in range(10):
            detector.execution_history.append({
                'timestamp': datetime.now().isoformat(),
                'success': True,
                'articles_found': 10,
                'articles_verified': 5,
                'processing_time_seconds': 60.0 + i,  # 少しずつ変化
                'error_message': None
            })
        
        detector._calculate_baseline()
        
        assert detector.baseline_performance is not None
        assert 'avg_processing_time' in detector.baseline_performance
        assert 'avg_articles_verified' in detector.baseline_performance
        assert detector.baseline_performance['avg_processing_time'] > 60.0
    
    def test_get_recent_alerts(self, detector):
        """最近のアラート取得のテスト"""
        # 古いアラート
        old_alert = {
            'type': 'test',
            'severity': 'warning',
            'message': 'Old alert',
            'details': {},
            'timestamp': (datetime.now() - timedelta(hours=25)).isoformat()
        }
        
        # 新しいアラート
        new_alert = {
            'type': 'test',
            'severity': 'warning',
            'message': 'New alert',
            'details': {},
            'timestamp': datetime.now().isoformat()
        }
        
        detector.alert_history = [old_alert, new_alert]
        
        recent = detector.get_recent_alerts(hours=24)
        
        assert len(recent) == 1
        assert recent[0]['message'] == 'New alert'
    
    def test_get_execution_stats(self, detector):
        """実行統計取得のテスト"""
        # いくつかの実行結果を追加
        for i in range(5):
            detector.execution_history.append({
                'timestamp': datetime.now().isoformat(),
                'success': i % 2 == 0,  # 交互に成功/失敗
                'articles_found': 10,
                'articles_verified': 5 if i % 2 == 0 else 0,
                'processing_time_seconds': 60.0,
                'error_message': None if i % 2 == 0 else "Error"
            })
        
        stats = detector.get_execution_stats()
        
        assert stats['total_executions'] == 5
        assert stats['successful_executions'] == 3
        assert stats['success_rate'] == 60.0
        assert 'recent_24h' in stats