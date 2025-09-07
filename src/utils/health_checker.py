"""
Health checker module for monitoring system status
"""
import requests
import subprocess
import time
from typing import Dict, List
from .logger import get_logger
from config.settings import HACKER_NEWS_API_URL, DEV_TO_API_URL

logger = get_logger(__name__)


class HealthChecker:
    """Class for checking system health and component availability"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def check_hacker_news_api(self) -> Dict:
        """Check Hacker News API availability"""
        try:
            start_time = time.time()
            response = self.session.get(f"{HACKER_NEWS_API_URL}/topstories.json", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'service': 'Hacker News API',
                    'status': 'healthy',
                    'response_time_ms': round(response_time * 1000, 2),
                    'stories_count': len(data) if isinstance(data, list) else 0,
                    'message': 'API responding normally'
                }
            else:
                return {
                    'service': 'Hacker News API',
                    'status': 'unhealthy',
                    'response_time_ms': round(response_time * 1000, 2),
                    'error': f'HTTP {response.status_code}',
                    'message': 'API returned error status'
                }
                
        except requests.RequestException as e:
            return {
                'service': 'Hacker News API',
                'status': 'unhealthy',
                'error': str(e),
                'message': 'API connection failed'
            }
    
    def check_dev_to_api(self) -> Dict:
        """Check dev.to API availability"""
        try:
            start_time = time.time()
            params = {'tag': 'ai', 'per_page': 1}
            response = self.session.get(DEV_TO_API_URL, params=params, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'service': 'dev.to API',
                    'status': 'healthy',
                    'response_time_ms': round(response_time * 1000, 2),
                    'articles_available': len(data) if isinstance(data, list) else 0,
                    'message': 'API responding normally'
                }
            else:
                return {
                    'service': 'dev.to API',
                    'status': 'unhealthy',
                    'response_time_ms': round(response_time * 1000, 2),
                    'error': f'HTTP {response.status_code}',
                    'message': 'API returned error status'
                }
                
        except requests.RequestException as e:
            return {
                'service': 'dev.to API',
                'status': 'unhealthy',
                'error': str(e),
                'message': 'API connection failed'
            }
    
    def check_medium_rss(self) -> Dict:
        """Check Medium RSS feed availability"""
        try:
            start_time = time.time()
            rss_url = "https://medium.com/feed/tag/ai"
            response = self.session.get(rss_url, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                # Simple check if content looks like RSS
                content_length = len(response.content)
                is_xml = b'<?xml' in response.content[:100]
                
                return {
                    'service': 'Medium RSS',
                    'status': 'healthy' if is_xml else 'degraded',
                    'response_time_ms': round(response_time * 1000, 2),
                    'content_length': content_length,
                    'message': 'RSS feed accessible' if is_xml else 'Response not XML format'
                }
            else:
                return {
                    'service': 'Medium RSS',
                    'status': 'unhealthy',
                    'response_time_ms': round(response_time * 1000, 2),
                    'error': f'HTTP {response.status_code}',
                    'message': 'RSS feed returned error status'
                }
                
        except requests.RequestException as e:
            return {
                'service': 'Medium RSS',
                'status': 'unhealthy',
                'error': str(e),
                'message': 'RSS feed connection failed'
            }
    
    def check_claude_cli(self) -> Dict:
        """Check Claude CLI availability"""
        try:
            start_time = time.time()
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if result.returncode == 0:
                version = result.stdout.strip()
                return {
                    'service': 'Claude CLI',
                    'status': 'healthy',
                    'response_time_ms': round(response_time * 1000, 2),
                    'version': version,
                    'message': 'Claude CLI available and configured'
                }
            else:
                return {
                    'service': 'Claude CLI',
                    'status': 'unhealthy',
                    'response_time_ms': round(response_time * 1000, 2),
                    'error': result.stderr.strip() if result.stderr else 'Unknown error',
                    'message': 'Claude CLI returned error'
                }
                
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return {
                'service': 'Claude CLI',
                'status': 'unhealthy',
                'error': str(e),
                'message': 'Claude CLI not available or not configured'
            }
    
    def check_system_resources(self) -> Dict:
        """Check basic system resource availability"""
        try:
            import psutil
            
            # Get CPU and memory usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine status based on resource usage
            status = 'healthy'
            warnings = []
            
            if cpu_percent > 80:
                status = 'degraded'
                warnings.append(f'High CPU usage: {cpu_percent}%')
            
            if memory.percent > 85:
                status = 'degraded'
                warnings.append(f'High memory usage: {memory.percent}%')
            
            if disk.percent > 90:
                status = 'degraded'
                warnings.append(f'High disk usage: {disk.percent}%')
            
            return {
                'service': 'System Resources',
                'status': status,
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'warnings': warnings,
                'message': 'System resources within normal limits' if status == 'healthy' else 'Resource usage elevated'
            }
            
        except ImportError:
            return {
                'service': 'System Resources',
                'status': 'unknown',
                'error': 'psutil not available',
                'message': 'Cannot check system resources (psutil not installed)'
            }
        except Exception as e:
            return {
                'service': 'System Resources',
                'status': 'unhealthy',
                'error': str(e),
                'message': 'Failed to check system resources'
            }
    
    def run_full_health_check(self) -> Dict:
        """Run comprehensive health check on all components"""
        logger.info("Starting comprehensive health check...")
        
        start_time = time.time()
        
        # Run all health checks
        checks = [
            self.check_hacker_news_api(),
            self.check_dev_to_api(),
            self.check_medium_rss(),
            self.check_claude_cli(),
            self.check_system_resources()
        ]
        
        total_time = time.time() - start_time
        
        # Calculate overall status
        healthy_count = sum(1 for check in checks if check['status'] == 'healthy')
        degraded_count = sum(1 for check in checks if check['status'] == 'degraded')
        unhealthy_count = sum(1 for check in checks if check['status'] == 'unhealthy')
        
        if unhealthy_count > 0:
            overall_status = 'unhealthy'
        elif degraded_count > 0:
            overall_status = 'degraded'
        else:
            overall_status = 'healthy'
        
        result = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S JST'),
            'overall_status': overall_status,
            'total_check_time_ms': round(total_time * 1000, 2),
            'summary': {
                'healthy': healthy_count,
                'degraded': degraded_count,
                'unhealthy': unhealthy_count,
                'total': len(checks)
            },
            'checks': checks
        }
        
        logger.info(f"Health check completed: {overall_status} ({healthy_count}/{len(checks)} healthy)")
        return result
    
    def get_health_status_emoji(self, status: str) -> str:
        """Get emoji representation of health status"""
        status_emojis = {
            'healthy': '✅',
            'degraded': '⚠️',
            'unhealthy': '❌',
            'unknown': '❓'
        }
        return status_emojis.get(status, '❓')
    
    def format_health_report(self, health_data: Dict) -> str:
        """Format health check results into readable report"""
        overall_emoji = self.get_health_status_emoji(health_data['overall_status'])
        
        report = f"""🏥 **AI News Feeder - System Health Report**
{overall_emoji} **Overall Status**: {health_data['overall_status'].upper()}
⏱️ **Check Duration**: {health_data['total_check_time_ms']}ms
📊 **Summary**: {health_data['summary']['healthy']}/{health_data['summary']['total']} services healthy

**Component Status:**"""
        
        for check in health_data['checks']:
            emoji = self.get_health_status_emoji(check['status'])
            service_name = check['service']
            status = check['status'].upper()
            message = check.get('message', 'No details available')
            
            report += f"\n{emoji} **{service_name}**: {status}"
            
            # Add specific details for each service
            if check['service'] == 'Hacker News API' and 'stories_count' in check:
                report += f" ({check['stories_count']} stories available)"
            elif check['service'] == 'dev.to API' and 'articles_available' in check:
                report += f" ({check['articles_available']} articles available)"
            elif check['service'] == 'Claude CLI' and 'version' in check:
                report += f" ({check['version']})"
            elif check['service'] == 'System Resources' and 'cpu_percent' in check:
                report += f" (CPU: {check['cpu_percent']}%, Memory: {check['memory_percent']}%)"
            
            if 'response_time_ms' in check:
                report += f" - {check['response_time_ms']}ms"
            
            if check['status'] != 'healthy' and 'error' in check:
                report += f"\n   ⚠️ Error: {check['error']}"
        
        report += f"\n\n📅 **Checked at**: {health_data['timestamp']}"
        
        return report
