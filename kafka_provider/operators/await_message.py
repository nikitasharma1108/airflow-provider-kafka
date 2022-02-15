from email import message_from_string
from typing import Any, Callable, Dict, Optional, Sequence
from functools import partial

from airflow.exceptions import AirflowException
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

from kafka_provider.triggers.await_message import AwaitMessageTrigger


VALID_COMMIT_CADENCE = {'never','end_of_batch','end_of_operator'}

class AwaitKafkaMessage(BaseOperator):

    BLUE = '#ffefeb'
    ui_color = BLUE

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
        xcom_push_key = None,
        **kwargs: Any
        ) -> None:
        super().__init__(**kwargs)
        
        self.topics = topics
        self.apply_function = apply_function
        self.apply_function_args = apply_function_args
        self.apply_function_kwargs = apply_function_kwargs
        self.kafka_conn_id = kafka_conn_id
        self.kafka_config = kafka_config
        self.poll_timeout = poll_timeout
        self.poll_interval = poll_interval
        self.xcom_push_key = xcom_push_key
        
    
        
    def execute(self, context) -> Any:

        self.defer(
            trigger=AwaitMessageTrigger(
                topics = self.topics,
                apply_function = self.apply_function ,
                apply_function_args =  self.apply_function_args ,
                apply_function_kwargs = self.apply_function_kwargs,
                kafka_conn_id = self.kafka_conn_id,
                kafka_config = self.kafka_config ,
                poll_timeout = self.poll_timeout ,
                poll_interval = self.poll_interval
            )
        )
    
    def execute_complete(self,context, event=None):
        if self.xcom_push_key:
            self.xcom_push(context, key=self.xcom_push_key, value=event)
        return event
