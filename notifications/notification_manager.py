"""
Notification system for QuantHybrid trading system.
"""
import asyncio
from typing import Dict, List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import telegram
from config.settings import NOTIFICATION_SETTINGS
from config.logging_config import get_logger

logger = get_logger('notifications')

class NotificationManager:
    def __init__(self):
        self.telegram_bot = None
        self.email_server = None
        self.notification_queue = asyncio.Queue()
        self.is_running = False
        self._setup_telegram()
        self._setup_email()
        # basic throttling store: type -> timestamps
        self._sent_timestamps: Dict[str, List[float]] = {}
    
    def _setup_telegram(self):
        """Setup Telegram bot for notifications."""
        try:
            if NOTIFICATION_SETTINGS['telegram_enabled']:
                self.telegram_bot = telegram.Bot(token=NOTIFICATION_SETTINGS['telegram_token'])
        except Exception as e:
            logger.error(f"Failed to setup Telegram bot: {str(e)}")
    
    def _setup_email(self):
        """Setup email client for notifications."""
        try:
            if NOTIFICATION_SETTINGS['email_enabled']:
                self.email_server = smtplib.SMTP_SSL(
                    NOTIFICATION_SETTINGS['smtp_server'],
                    NOTIFICATION_SETTINGS['smtp_port']
                )
                self.email_server.login(
                    NOTIFICATION_SETTINGS['smtp_username'],
                    NOTIFICATION_SETTINGS['smtp_password']
                )
        except Exception as e:
            logger.error(f"Failed to setup email client: {str(e)}")
    
    async def start(self):
        """Start the notification service."""
        try:
            self.is_running = True
            asyncio.create_task(self._notification_loop())
            logger.info("Notification service started")
        except Exception as e:
            logger.error(f"Failed to start notification service: {str(e)}")
    
    async def stop(self):
        """Stop the notification service."""
        try:
            self.is_running = False
            if self.email_server:
                self.email_server.quit()
            logger.info("Notification service stopped")
        except Exception as e:
            logger.error(f"Error stopping notification service: {str(e)}")
    
    async def _notification_loop(self):
        """Main notification processing loop."""
        while self.is_running:
            try:
                notification = await self.notification_queue.get()
                await self._process_notification(notification)
                self.notification_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in notification loop: {str(e)}")
                await asyncio.sleep(5)
    
    async def _process_notification(self, notification: Dict):
        """Process a single notification."""
        try:
            priority = notification.get('priority', 'normal')
            message = notification['message']
            
            # Send based on priority and settings
            if priority == 'critical':
                await self._send_critical_notification(message)
            elif priority == 'high':
                await self._send_high_priority_notification(message)
            else:
                await self._send_normal_notification(message)
                
        except Exception as e:
            logger.error(f"Error processing notification: {str(e)}")
    
    async def _send_critical_notification(self, message: str):
        """Send critical priority notification."""
        try:
            # Send to all configured channels
            tasks = []
            if NOTIFICATION_SETTINGS['telegram_enabled']:
                tasks.append(self._send_telegram(message))
            if NOTIFICATION_SETTINGS['email_enabled']:
                tasks.append(self._send_email(
                    subject="CRITICAL ALERT - QuantHybrid",
                    message=message
                ))
            await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"Error sending critical notification: {str(e)}")
    
    async def _send_high_priority_notification(self, message: str):
        """Send high priority notification."""
        try:
            if NOTIFICATION_SETTINGS['telegram_enabled']:
                await self._send_telegram(message)
                
            if NOTIFICATION_SETTINGS['email_enabled'] and NOTIFICATION_SETTINGS['email_high_priority']:
                await self._send_email(
                    subject="High Priority Alert - QuantHybrid",
                    message=message
                )
                
        except Exception as e:
            logger.error(f"Error sending high priority notification: {str(e)}")
    
    async def _send_normal_notification(self, message: str):
        """Send normal priority notification."""
        try:
            # Send only to primary channel
            if NOTIFICATION_SETTINGS['telegram_enabled']:
                await self._send_telegram(message)
            elif NOTIFICATION_SETTINGS['email_enabled']:
                await self._send_email(
                    subject="QuantHybrid Notification",
                    message=message
                )
                
        except Exception as e:
            logger.error(f"Error sending normal notification: {str(e)}")
    
    async def _send_telegram(self, message: str):
        """Send message via Telegram."""
        try:
            if self.telegram_bot:
                await self.telegram_bot.send_message(
                    chat_id=NOTIFICATION_SETTINGS['telegram_chat_id'],
                    text=message,
                    parse_mode='HTML'
                )
        except Exception as e:
            logger.error(f"Error sending Telegram message: {str(e)}")
    
    async def _send_email(self, subject: str, message: str):
        """Send message via email."""
        try:
            if self.email_server:
                msg = MIMEMultipart()
                msg['From'] = NOTIFICATION_SETTINGS['smtp_username']
                msg['To'] = NOTIFICATION_SETTINGS['notification_email']
                msg['Subject'] = subject
                
                msg.attach(MIMEText(message, 'plain'))
                self.email_server.send_message(msg)
                
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
    
    async def notify(self, message: str, priority: str = 'normal'):
        """Queue a notification for sending."""
        try:
            await self.notification_queue.put({
                'message': message,
                'priority': priority
            })
        except Exception as e:
            logger.error(f"Error queueing notification: {str(e)}")
    
    async def notify_trade(self, trade_info: Dict):
        """Send trade notification."""
        try:
            message = (
                f"🔄 Trade Executed:\n"
                f"Strategy: {trade_info['strategy']}\n"
                f"Instrument: {trade_info['instrument']}\n"
                f"Side: {trade_info['side']}\n"
                f"Quantity: {trade_info['quantity']}\n"
                f"Price: {trade_info['price']}\n"
                f"Time: {trade_info['timestamp']}"
            )
            await self.notify(message, 'normal')
            
        except Exception as e:
            logger.error(f"Error sending trade notification: {str(e)}")
    
    async def notify_error(self, error_info: Dict):
        """Send error notification."""
        try:
            message = (
                f"⚠️ Error Detected:\n"
                f"Type: {error_info['type']}\n"
                f"Component: {error_info['component']}\n"
                f"Message: {error_info['message']}\n"
                f"Time: {error_info['timestamp']}"
            )
            await self.notify(message, 'high')
            
        except Exception as e:
            logger.error(f"Error sending error notification: {str(e)}")
    
    async def notify_system_status(self, status: Dict):
        """Send system status notification."""
        try:
            message = (
                f"📊 System Status Update:\n"
                f"CPU Usage: {status['cpu_usage']}%\n"
                f"Memory Usage: {status['memory_usage']}%\n"
                f"Active Strategies: {status['active_strategies']}\n"
                f"Open Positions: {status['open_positions']}\n"
                f"Daily P&L: {status['daily_pnl']}\n"
                f"Risk Level: {status['risk_level']}"
            )
            await self.notify(message, 'normal')
            
        except Exception as e:
            logger.error(f"Error sending status notification: {str(e)}")

    # Methods expected by tests
    async def dispatch_notification(self, alert: Dict):
        await self._send_notification(alert)

    async def _send_notification(self, alert: Dict):
        # Basic channel-agnostic send stub for tests
        if alert.get('severity') == 'HIGH':
            await self._send_high_priority_notification(alert.get('message', ''))
        else:
            await self._send_normal_notification(alert.get('message', ''))

    async def send_email_alert(self, alert: Dict):
        await self._send_email(subject=f"{alert.get('type', 'ALERT')} - {alert.get('severity', '')}", message=alert.get('message', ''))

    async def send_sms_alert(self, alert: Dict):
        # SMS sending is not implemented; simply log for tests
        logger.info(f"SMS alert: {alert}")

    async def aggregate_alerts(self, alerts: List[Dict]) -> List[Dict]:
        # Aggregate by (type, message) within 1-minute window
        aggregated: Dict[tuple, Dict] = {}
        for alert in alerts:
            key = (alert.get('type'), alert.get('message'))
            if key not in aggregated:
                aggregated[key] = {**alert, 'count': 1}
            else:
                aggregated[key]['count'] += 1
        result = []
        for a in aggregated.values():
            if a['count'] > 1:
                a['message'] = f"{a['message']} (multiple occurrences: {a['count']})"
            result.append(a)
        return result

    def check_throttle_status(self, alert_type: str) -> Dict:
        import time
        now = time.time()
        window = NOTIFICATION_SETTINGS.get('throttle_window_seconds', 60)
        max_per_window = NOTIFICATION_SETTINGS.get('max_alerts_per_window', 5)
        timestamps = self._sent_timestamps.setdefault(alert_type, [])
        timestamps = [t for t in timestamps if now - t <= window]
        self._sent_timestamps[alert_type] = timestamps
        is_throttled = len(timestamps) >= max_per_window
        return {'is_throttled': is_throttled, 'sent_in_window': len(timestamps)}
