"""Communication with kinesis service."""
from briefy.reflex import logger
from briefy.reflex.celery import app
from briefy.reflex.tasks import ReflexTask

import boto3
import json


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
        self._empty_shards = []

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
        """Stream shard ids."""
        return [
            shard for shard in self.description.get('Shards', [])
            if shard['ShardId'] not in self._empty_shards
        ]

    def run(self, item_callback=None):
        """Start processing all shards."""
        self.item_callback = item_callback
        logger.info('Starting consumer. Use CTRL+C to stop.')
        while self.shards:
            # time.sleep(0.5)
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
            self._empty_shards.append(shard_id)
        else:
            for item in records:
                if self.item_callback:
                    data = json.loads(item.get('Data'))
                    order = data.get('order')
                    contents = data.get('contents')
                    self.item_callback(order, contents)
                self._sequences[shard_id] = item['SequenceNumber']

        next_shard_iterator = response['NextShardIterator']
        self._iterators[shard_id] = next_shard_iterator


if __name__ == '__main__':
    # IMPORTANT: to load the data into kinesis
    # uri = 'https://s3.eu-central-1.amazonaws.com/ms-ophelie-live/reports/leica/finance/20171023/20171023003100-orders-all.csv'  # noQA
    # from briefy.reflex.tasks.leica import read_all_delivery_contents
    # read_all_delivery_contents(uri)

    TOTAL_IMG_PER_ORDER = {}
    TO_DEBUG_LINKS = {}
    TO_DEBUG_ZERO = {}
    FOLDER_NAMES = [
        'originals', 'original', 'jpeg', 'original sizes',
        'original size', 'original format', 'PRINT'
    ]

    def callback(order, contents):
        """Compute the values for each order."""
        order_id = order.get('uid')
        number_images = len(contents.get('images'))
        # sub_folders = [
        #    folder for folder in contents.get('folders')
        #    if folder.get('name').lower().strip() in FOLDER_NAMES
        # ]
        sub_folders = contents.get('folders')
        number_additional_images = sum([len(folder.get('images')) for folder in sub_folders])
        total_images = number_images + number_additional_images
        TOTAL_IMG_PER_ORDER[order_id] = {
            'total_images': total_images
        }
        all_sub_folders = [folder.get('name') for folder in contents.get('folders')]
        if total_images <= 1:
            data = {
                'folders': all_sub_folders,
                'delivery_link': order.get('delivery_link')
            }
            if all_sub_folders:
                TO_DEBUG_LINKS[order_id] = data
            else:
                TO_DEBUG_ZERO[order_id] = data
            logger.info(order_id)
            logger.info(order.get('delivery_link'))
            logger.info(all_sub_folders)

    c = KinesisConsumer(GDRIVE_DELIVERY_STREAM)
    c.run(callback)

    TOTAL_IMG = sum([value.get('total_images') for value in TOTAL_IMG_PER_ORDER.values()])
    logger.info(f'Total of images found: {TOTAL_IMG}')
