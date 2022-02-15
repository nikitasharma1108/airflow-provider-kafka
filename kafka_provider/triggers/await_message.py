import asyncio
from functools import partial
from asyncore import poll
from os import sync
from typing import Any, Dict, Optional, Tuple, Union, Callable, Sequence

from airflow import AirflowException
from airflow.triggers.base import BaseTrigger, TriggerEvent

from asgiref.sync import sync_to_async
from kafka_provider.hooks.consumer import ConsumerHook
from kafka_provider.shared_utils import get_callable



class AwaitMessageTrigger(BaseTrigger):

    def __init__(
        self,
        topics: Sequence[str],
        apply_function: str,
        apply_function_args: Sequence[Any],
        apply_function_kwargs: Dict[Any,Any],
        kafka_conn_id: Optional[str] = None,
        kafka_config: Optional[Dict[Any,Any]] = None,
        poll_timeout: float = 1,
        poll_interval: float = 5,
    )-> None:

        self.topics = topics
        self.apply_function = apply_function
        self.apply_function_args = apply_function_args
        self.apply_function_kwargs = apply_function_kwargs
        self.kafka_conn_id = kafka_conn_id
        self.kafka_config = kafka_config
        self.poll_timeout = poll_timeout
        self.poll_interval = poll_interval


    def serialize(self) -> Tuple[str, Dict[str, Any]]:
        return(
            'kafka_provider.triggers.await_message.AwaitMessageTrigger',
            {
            "topics" : self.topics,
            "apply_function" : self.apply_function,
            "apply_function_args" : self.apply_function_args,
            "apply_function_kwargs" : self.apply_function_kwargs,
            "kafka_conn_id" : self.kafka_conn_id,
            "kafka_config" : self.kafka_config,
            "poll_timeout" : self.poll_timeout,
            "poll_interval" : self.poll_interval
            }
        )


    async def run(self):
        consumer_hook = ConsumerHook(topics = self.topics, kafka_conn_id=self.kafka_conn_id, config=self.kafka_config, no_broker=self.no_broker)
        
        async_get_consumer = sync_to_async(consumer_hook.get_consumer)
        consumer = await async_get_consumer()

        async_poll = sync_to_async(consumer.poll)
        async_commit = sync_to_async(consumer.commit)

        processing_call = get_callable(self.apply_function)
        processing_call = partial(processing_call,*self.apply_function_args, **self.apply_function_kwargs)
        async_message_process = sync_to_async(processing_call)
        while True:

            message = await async_poll(self.poll_timeout)

            rv = await async_message_process(message)
            if rv:
                yield TriggerEvent(rv)
                await async_commit(asynchronous=False)
            elif rv is None:
                await async_commit(asynchronous=False)
                await asyncio.sleep(self.poll_interval)
            else:
                await async_commit(asynchronous=False)
                
            

    
 