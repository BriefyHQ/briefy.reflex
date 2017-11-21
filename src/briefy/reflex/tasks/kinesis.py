"""Communication with kinesis service."""
from briefy.reflex import logger
from briefy.reflex.celery import app
from briefy.reflex.config import GDRIVE_DELIVERY_STREAM
from briefy.reflex.tasks import ReflexTask
from collections import namedtuple
from dateutil import parser
from datetime import datetime

import boto3
import csv
import json
import pytz


FOLDER_NAMES = [
    'originals', 'original', 'jpeg', 'original sizes', 'original size', 'original format', 'PRINT'
]


@app.task(base=ReflexTask, rate_limit='10/s')
def put_gdrive_record(result: tuple, stream: str=GDRIVE_DELIVERY_STREAM) -> bool:
    """Put gdrive folder contents and orders data in a kinesis stream.

    :param result: data tuple
    :param stream: kinesis stream name
    :return: True if success and False if failed
    """
    order, contents = result
    data = {
        'contents': contents,
        'order': order,
    }
    order_id = order.get('id')
    client = boto3.client('kinesis')
    response = client.put_record(
        Data=json.dumps(data),
        PartitionKey=order_id,
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
        shard_iterator, date = self._iterators.get(shard_id, (None, None))
        if shard_iterator and date:
            # validate iterator datetime and
            date = parser.parse(date)
            now = datetime.now().astimezone(pytz.utc)
            date_diff = (now - date).seconds
            if date_diff > 280:
                shard_iterator = None

        if not (shard_iterator and date):
            client = self.client
            sequence_number = self.get_sequence(shard)
            response = client.get_shard_iterator(
                StreamName=self.stream,
                ShardId=shard_id,
                ShardIteratorType='AT_SEQUENCE_NUMBER',
                StartingSequenceNumber=sequence_number,
            )
            date = response.get('ResponseMetadata').get('HTTPHeaders').get('date')
            shard_iterator = response['ShardIterator']
            self._iterators[shard_id] = shard_iterator, date

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
        date = response.get('ResponseMetadata').get('HTTPHeaders').get('date')
        self._iterators[shard_id] = next_shard_iterator, date


TotalAssets = namedtuple('TotalAssets', ['images', 'videos', 'others'])


def count_assets(contents, filter_folders=False) -> TotalAssets:
    """Count the number of assets in the gdrive folder contents result.

    :param contents: briefy.gdrive.api.contents result.
    :param filter_folders: only count images on folders with specific names.
    :return: total number of images in the folder and sub folders.
    """
    if filter_folders:
        sub_folders = [
            folder for folder in contents.get('folders')
            if folder.get('name').lower().strip() in FOLDER_NAMES
        ]
    else:
        sub_folders = contents.get('folders', [])

    total = TotalAssets(
        len(contents.get('images', [])) + sum(
            [len(folder.get('images', [])) for folder in sub_folders]
        ),
        len(contents.get('videos', [])) + sum(
            [len(folder.get('videos', [])) for folder in sub_folders]
        ),
        len(contents.get('other_files', [])) + sum(
            [len(folder.get('other_files', [])) for folder in sub_folders]
        )
    )

    if total.images == 0:
        import pdb; pdb.set_trace()

    return total


def export_csv(data: dict, file_path: str):
    """Export a map of orders to csv.

    :param data: dict with key, value pairs to be exported, each value should be a dict also
    :param file_path: complete file path to save the export.
    :return:
    """
    fieldnames = [
        'briefy_id', 'number_required_assets', 'number_submissions', 'total_submissions_images',
        'total_submissions_videos', 'total_submissions_others', 'total_archive_images',
        'total_archive_videos', 'total_archive_others', 'total_delivery_images',
        'total_delivery_videos', 'total_delivery_others', 'submission_links', 'archive_link',
        'delivery_link', 'order_link'
    ]

    with open(file_path, 'w') as fout:
        writer = csv.DictWriter(fout, fieldnames)
        writer.writeheader()
        for key, value in data.items():
            writer.writerow(value)


if __name__ == '__main__':
    # IMPORTANT: to load the data into kinesis
    # uri = 'https://s3.eu-central-1.amazonaws.com/ms-ophelie-dev/reports/leica/finance/20171120/20171120180500-orders-all.csv'  # noQA
    # from briefy.reflex.tasks.leica import read_all_delivery_contents
    # read_all_delivery_contents(uri)

    TOTAL_IMG_PER_ORDER = {}
    TO_DEBUG_LINKS = {}
    TO_DEBUG_ZERO = {}
    TO_DEBUG_ARCHIVE = {}
    TO_DEBUG_SUBMISSION = {}

    def callback(order, contents):
        """Compute the values for each order."""
        order_id = order.get('slug')
        delivery = order.get('delivery')
        number_required_assets = order.get('number_required_assets')
        total_delivery = count_assets(contents.get('delivery'))
        submissions = contents.get('submissions')
        total_submissions = [count_assets(submission) for submission in submissions]
        total_archive = count_assets(contents.get('archive'))
        submission_links = ','.join(
            [str(a.get('submission_path', 'null')) for a in order.get('assignments')]
        )

        data = {
            'total_delivery_images': total_delivery.images,
            'total_delivery_videos': total_delivery.videos,
            'total_delivery_others': total_delivery.others,
            'total_archive_images': total_archive.images,
            'total_archive_videos': total_archive.videos,
            'total_archive_others': total_archive.others,
            'total_submissions_images': sum([item.images for item in total_submissions]),
            'total_submissions_videos': sum([item.videos for item in total_submissions]),
            'total_submissions_others': sum([item.others for item in total_submissions]),
            'number_submissions': len(submissions),
            'briefy_id': order_id,
            'delivery_link': delivery.get('gdrive'),
            'archive_link': delivery.get('archive'),
            'submission_links': submission_links,
            'number_required_assets': number_required_assets,
            'order_link': f'https://app.briefy.co/orders/{order.get("id")}'
        }
        TOTAL_IMG_PER_ORDER[order_id] = data

        if not total_delivery.images:
            TO_DEBUG_ZERO[order_id] = data
        elif total_delivery.images > total_archive.images:
            TO_DEBUG_ARCHIVE[order_id] = data
        elif data['total_submissions_images'] == 0:
            TO_DEBUG_SUBMISSION[order_id] = data

        logger.info(f'Order id {order_id} processed. Number of images: {total_delivery}')

    c = KinesisConsumer(GDRIVE_DELIVERY_STREAM)
    c.run(callback)

    export_csv(TOTAL_IMG_PER_ORDER, '/tmp/orders-image-inventory.csv')
    export_csv(TO_DEBUG_ARCHIVE, '/tmp/orders-inventory-check-archive.csv')
    export_csv(TO_DEBUG_SUBMISSION, '/tmp/orders-inventory-check-submission.csv')
    export_csv(TO_DEBUG_ZERO, '/tmp/orders-inventory-zero-images.csv')

    TOTAL_IMG = sum([value.get('total_delivery_images') for value in TOTAL_IMG_PER_ORDER.values()])
    logger.info(f'Total of delivery images found: {TOTAL_IMG}')
