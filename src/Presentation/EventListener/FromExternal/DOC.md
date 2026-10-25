
## 1.7. How to use KafkaConsumerService

The `KafkaConsumerService` is a builder-pattern implementation for creating Kafka consumers. It provides a fluent interface for configuring and managing Kafka consumers.

### Minimal Example
```python
from Presentation.Queues.Services.KafkaConsumerService import KafkaConsumerService
from Presentation.Queues.Collections.ExampleTopicCollection import ExampleTopicCollection

async def handle_message(message: ExampleTopicCollection):
    print(f"Received message: {message}")

# Create and start the consumer
consumer = KafkaConsumerService[ExampleTopicCollection]() \
    .with_topic("my-topic") \
    .with_bootstrap_servers("localhost:9092") \
    .with_group_id("my-group") \
    .with_handler(handle_message)

await consumer.start()

# Later, when you want to stop
await consumer.stop()
```

### Complete Example with All Options
```python
from Presentation.Queues.Services.KafkaConsumerService import KafkaConsumerService
from Presentation.Queues.Collections.ExampleTopicCollection import ExampleTopicCollection
import json
import asyncio

async def handle_message(message: ExampleTopicCollection):
    print(f"Processing message: {message}")
    # Your message processing logic here

def custom_deserializer(value: bytes) -> dict:
    return json.loads(value.decode('utf-8'))

async def main():
    # Create consumer with all available options
    consumer = KafkaConsumerService[ExampleTopicCollection]() \
        .with_topic("my-topic") \
        .with_bootstrap_servers("localhost:9092") \
        .with_group_id("my-group") \
        .with_handler(handle_message) \
        .with_client_id("my-custom-client") \
        .with_value_deserializer(custom_deserializer)

    try:
        # Start consuming messages
        await consumer.start()
        
        # Keep the consumer running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        # Gracefully stop the consumer
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(main())

### Key Features
- **Builder Pattern**: Fluent interface for configuration
- **Type Safety**: Generic type support for message models
- **Validation**: Required fields are validated before starting
- **Async Support**: Built-in async/await support
- **Error Handling**: Built-in error handling and logging
- **Graceful Shutdown**: Proper cleanup on stop

### Available Builder Methods
- `with_topic(topic: Union[str, List[str]])`: Set the Kafka topic(s) to consume from
- `with_bootstrap_servers(bootstrap: str)`: Set the Kafka bootstrap servers
- `with_group_id(group_id: str)`: Set the consumer group ID
- `with_handler(handler: Callable[[T], Awaitable[Any]])`: Set the message handler function
- `with_value_deserializer(deserializer: Callable[[bytes], Any])`: Set custom message deserializer
- `with_client_id(client_id: str)`: Set custom client ID

### Lifecycle Methods
- `start()`: Start consuming messages
- `stop()`: Stop consuming messages and clean up resources