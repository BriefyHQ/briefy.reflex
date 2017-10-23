"""Communication with kinesis service."""
from briefy.reflex import logger
from briefy.reflex.celery import app
from briefy.reflex.tasks import ReflexTask

import boto3
import json
import time


GDRIVE_DELIVERY_STREAM = 'gdrive_delivery_contents_live'


@app.task(base=ReflexTask)
def put_gdrive_record(contents: dict, order: dict, stream: str=GDRIVE_DELIVERY_STREAM) -> bool:
    """Put gdrive folder contents and orders data in a kinesis stream.

    :param contents: gdrive folder contents payload
    :param order: order payload
    :param stream: kinesis stream name
    :return: True if success and False if failed
    """
    data = {
        'order': order,
        'contents': contents,
    }

    client = boto3.client('kinesis')
    response = client.put_record(
        Data=json.dumps(data),
        PartitionKey=order.get('uid'),
        StreamName=stream
    )
    success = response['ResponseMetadata']['HTTPStatusCode'] == 200
    return success if success else False


class KinesisConsumer:
    """Consume a kinesis stream."""

    def __init__(self, stream: str):
        """Initialize consumer."""
        self.client = boto3.client('kinesis')
        self.stream = stream
        self.update()
        self._iterators = {}

        # TODO: this should be persisted
        self._sequences = {}

    def update(self):
        """Update describe information from AWS in the class."""
        try:
            response = self.client.describe_stream(StreamName=self.stream)
        except Exception as exc:
            logger.exception(f'Failure trying to get stream: "{self.stream}".', exc)
        else:
            if response['ResponseMetadata']['HTTPStatusCode'] != 200:
                logger.error(f'Failure to describe stream "{self.stream}": {response}')
            else:
                self.description = response['StreamDescription']

    def get_sequence(self, shard: dict) -> str:
        """Get sequence number for a given shard.

        :param shard: shard data payload from describe_stream
        :return: latest sequence number for this shard
        """
        shard_id = shard['ShardId']
        sequence_number = self._sequences.get(shard_id)
        if not sequence_number:
            sequence_number = shard['SequenceNumberRange']['StartingSequenceNumber']
            self._sequences[shard_id] = sequence_number
        return sequence_number

    def get_iterator(self, shard: dict) -> str:
        """Get shard iterator for a given shard.

        :param shard: shard data payload from describe_stream
        :return: shard iterator id
        """
        shard_id = shard['ShardId']
        shard_iterator = self._iterators.get(shard_id)
        if not shard_iterator:
            client = self.client
            sequence_number = self.get_sequence(shard)
            response = client.get_shard_iterator(
                StreamName=self.stream,
                ShardId=shard_id,
                ShardIteratorType='AT_SEQUENCE_NUMBER',
                StartingSequenceNumber=sequence_number,
            )
            shard_iterator = response['ShardIterator']
        return shard_iterator

    @property
    def shards(self) -> list:
        """Stream shard ids"""
        return self.description.get('Shards', [])

    def run(self):
        """Start processing all shards."""
        logger.info('Starting consumer. Use CTRL+C to stop.')
        while True:
            time.sleep(0.5)
            for shard in self.shards:
                shard_id = shard['ShardId']
                shard_iterator = self.get_iterator(shard)
                self.process_records(shard_iterator, shard_id)

    def process_records(self, shard_iterator: str, shard_id: str):
        """Process records from a shard iterator."""
        response = self.client.get_records(
            ShardIterator=shard_iterator
        )

        logger.debug('Getting data from shard: {shard_id}', extra=response)
        records = response['Records']

        if len(records) == 0:
            logger.info(f'Nothing to process for shard: "{shard_id}"')
        else:
            for item in records:
                logger.info(str(item))
                self._sequences[shard_id] = item['SequenceNumber']

        next_shard_iterator = response['NextShardIterator']
        self._iterators[shard_id] = next_shard_iterator


if __name__ == '__main__':
    c = KinesisConsumer(GDRIVE_DELIVERY_STREAM)
    c.run()
