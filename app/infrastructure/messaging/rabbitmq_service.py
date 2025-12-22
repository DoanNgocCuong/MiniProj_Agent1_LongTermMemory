"""
RabbitMQ service for message queue operations.
Handles connection, publishing, and consuming messages.
"""
import json
import pika
import pika.exceptions
from typing import Any, Callable, Dict, Optional
from pika.adapters.asyncio_connection import AsyncioConnection
from pika.connection import ConnectionParameters
from pika.credentials import PlainCredentials

from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import MessageQueueError

logger = get_logger(__name__)


class RabbitMQService:
    """
    RabbitMQ service for async message queue operations.
    Handles connection management and message publishing/consuming.
    """
    
    def __init__(self):
        """Initialize RabbitMQ service."""
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
        self._connected = False
    
    def connect(self, raise_on_error: bool = True) -> bool:
        """
        Connect to RabbitMQ server.
        
        Args:
            raise_on_error: If True, raise exception on error. If False, return False.
        
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            # Use properties to get username/password (supports both naming conventions)
            username = settings.RABBITMQ_USER
            password = settings.RABBITMQ_PASS
            
            credentials = PlainCredentials(
                username,
                password,
            )
            parameters = ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                virtual_host=settings.RABBITMQ_VHOST,
                credentials=credentials,
            )
            
            # Log connection attempt (without password)
            logger.info(
                f"Connecting to RabbitMQ: host={settings.RABBITMQ_HOST}, "
                f"port={settings.RABBITMQ_PORT}, user={username}, "
                f"vhost={settings.RABBITMQ_VHOST}"
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare exchange if configured
            if settings.RABBITMQ_EXCHANGE:
                self.channel.exchange_declare(
                    exchange=settings.RABBITMQ_EXCHANGE,
                    exchange_type='direct',
                    durable=True,
                )
                logger.info(f"Declared exchange: {settings.RABBITMQ_EXCHANGE}")
            
            # Declare queue with durability
            queue_name = settings.RABBITMQ_QUEUE_NAME
            self.channel.queue_declare(
                queue=queue_name,
                durable=True,  # Queue survives broker restart
            )
            
            # Bind queue to exchange if both are configured
            if settings.RABBITMQ_EXCHANGE:
                self.channel.queue_bind(
                    exchange=settings.RABBITMQ_EXCHANGE,
                    queue=queue_name,
                    routing_key=queue_name,
                )
                logger.info(f"Bound queue {queue_name} to exchange {settings.RABBITMQ_EXCHANGE}")
            
            # Set QoS to prevent overwhelming workers
            self.channel.basic_qos(prefetch_count=settings.RABBITMQ_PREFETCH_COUNT)
            
            self._connected = True
            logger.info("RabbitMQ connected successfully")
            return True
        except pika.exceptions.ProbableAuthenticationError as e:
            username = settings.RABBITMQ_USER
            logger.error(
                f"RabbitMQ authentication failed: host={settings.RABBITMQ_HOST}, "
                f"port={settings.RABBITMQ_PORT}, user={username}. "
                f"Please check your credentials in .env file (RABBITMQ_USERNAME/RABBITMQ_DEFAULT_USER, RABBITMQ_PASSWORD/RABBITMQ_DEFAULT_PASS)"
            )
            self._connected = False
            if raise_on_error:
                raise MessageQueueError(
                    f"RabbitMQ authentication failed. Check RABBITMQ_DEFAULT_USER and RABBITMQ_DEFAULT_PASS in .env"
                ) from e
            return False
        except Exception as e:
            logger.error(
                f"Failed to connect to RabbitMQ: host={settings.RABBITMQ_HOST}, "
                f"port={settings.RABBITMQ_PORT}, error={e}"
            )
            self._connected = False
            if raise_on_error:
                raise MessageQueueError(f"Failed to connect to RabbitMQ: {e}") from e
            return False
    
    def disconnect(self) -> None:
        """Disconnect from RabbitMQ."""
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.close()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            self._connected = False
            logger.info("RabbitMQ disconnected")
        except Exception as e:
            logger.warning(f"Error disconnecting from RabbitMQ: {e}")
    
    def publish(
        self,
        message: Dict[str, Any],
        queue: Optional[str] = None,
        routing_key: Optional[str] = None,
        raise_on_error: bool = False,
    ) -> bool:
        """
        Publish message to queue.
        
        Args:
            message: Message dictionary to publish
            queue: Queue name (defaults to extraction queue)
            routing_key: Routing key (defaults to queue name)
            raise_on_error: If True, raise exception on error. If False, return False.
        
        Returns:
            True if published successfully, False otherwise
        """
        if not self._connected:
            if not self.connect(raise_on_error=False):
                if raise_on_error:
                    raise MessageQueueError("RabbitMQ is not connected")
                logger.warning("RabbitMQ not connected, skipping message publish")
                return False
        
        queue = queue or settings.RABBITMQ_QUEUE_NAME
        routing_key = routing_key or queue
        
        try:
            # Serialize message to JSON
            body = json.dumps(message, ensure_ascii=False, default=str)
            
            # Use exchange if configured, otherwise use default exchange
            exchange = settings.RABBITMQ_EXCHANGE or ""
            
            # Publish with persistence
            self.channel.basic_publish(
                exchange=exchange,
                routing_key=routing_key,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                ),
            )
            logger.info(
                f"Published message to exchange='{exchange}', queue='{queue}', "
                f"routing_key='{routing_key}': {message.get('job_id', 'unknown')}"
            )
            return True
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            self._connected = False  # Mark as disconnected
            if raise_on_error:
                raise MessageQueueError(f"Failed to publish message: {e}") from e
            return False
    
    def consume(
        self,
        callback: Callable[[Dict[str, Any]], None],
        queue: Optional[str] = None,
        auto_ack: bool = False,
    ) -> None:
        """
        Start consuming messages from queue.
        
        Args:
            callback: Callback function to process messages
            queue: Queue name (defaults to extraction queue)
            auto_ack: Whether to auto-acknowledge messages
        """
        if not self._connected:
            self.connect()
        
        queue = queue or settings.RABBITMQ_QUEUE_NAME
        
        def on_message(
            ch: pika.channel.Channel,
            method: pika.spec.Basic.Deliver,
            properties: pika.spec.BasicProperties,
            body: bytes,
        ) -> None:
            """Handle incoming message."""
            try:
                # Deserialize message
                message = json.loads(body.decode())
                logger.info(f"Received message from queue '{queue}': {message.get('job_id', 'unknown')}")
                
                # Call callback
                callback(message)
                
                # Acknowledge message
                if not auto_ack:
                    ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error processing message: {error_msg}")
                
                # Check if this is a permanent error (should not requeue)
                # NOTE:
                # - "Permanent processing error" and event loop issues are already treated as permanent
                # - "Job not found" means the job record does not exist in DB and will not appear later,
                #   so requeuing would create an infinite retry loop ⇒ treat as permanent as well.
                is_permanent_error = (
                    "Permanent processing error" in error_msg
                    or "attached to a different loop" in error_msg
                    or "Job not found" in error_msg
                )
                
                # Reject message
                if not auto_ack:
                    if is_permanent_error:
                        # Don't requeue permanent errors - send to dead letter queue or discard
                        logger.warning(
                            f"Permanent error detected, message will not be requeued: "
                            f"job_id={message.get('job_id', 'unknown')}"
                        )
                        ch.basic_nack(
                            delivery_tag=method.delivery_tag,
                            requeue=False,  # Don't requeue permanent errors
                        )
                    else:
                        # Requeue transient errors
                        ch.basic_nack(
                            delivery_tag=method.delivery_tag,
                            requeue=True,
                        )
        
        try:
            self.channel.basic_consume(
                queue=queue,
                on_message_callback=on_message,
                auto_ack=auto_ack,
            )
            logger.info(f"Started consuming from queue '{queue}'")
            self.channel.start_consuming()
        except Exception as e:
            logger.error(f"Error consuming messages: {e}")
            raise MessageQueueError(f"Failed to consume messages: {e}") from e
    
    def stop_consuming(self) -> None:
        """Stop consuming messages."""
        if self.channel and self.channel.is_consuming:
            self.channel.stop_consuming()
            logger.info("Stopped consuming messages")


# Global RabbitMQ service instance
rabbitmq_service = RabbitMQService()


def get_rabbitmq_service() -> RabbitMQService:
    """Get RabbitMQ service instance."""
    # Don't auto-connect, let publish() handle connection with graceful error handling
    return rabbitmq_service

