=======
History
=======

1.0.0 (2017-12-19)
------------------

    * Celery code to define app, config, worker and tasks module (rudaporto).
    * Task module to query orders accepted on Leica (rudaporto).
    * Task module to query in google drive folder contents of delivery folder (rudaporto).
    * Task module to add collections and assets in briefy.alexandria from Leica Orders payload (rudaporto).
    * Added Dockerfile, Procfile and docker scripts to execute celery tasks_worker (rudaporto).
    * Added new task to download file from gdrive api and save in the file system (rudaporto).
    * Added new task to upload file from the file system to amazon s3 bucket (rudaporto).
    * Updated tasks.alexandria.create_assets to create a chain to add_or_update_assets, download from gdrive and upload to s3 (rudaporto).
    * Added queue reader for briefy.reflex (rudaporto).
    * Added dispatch worker for briefy.reflex with new entry point, docker script, newrelic config and Procfile entry (rudaporto).
    * Added result events for briefy.reflex (rudaporto).
    * Added function to read data from orders csv report and query google drive delivery folder and store result on kinesis (rudaporto).
    * Added initial consumer to read data from kinesis (rudaporto).
    * Added to gdrive a new task to move a file to a new folder (rudaporto).
    * Added to gdrive a function to build a group task to move all files from one folder to another (rudaporto).
    * Update task to load all data to kinesis to also include a full order payload (rudaporto).
    * Update briefy.common and briefy.gdrive versions to latest stable (rudaporto).
    * Include archive and submission folder in the task to get assets contents from gdrive (rudaporto).
    * Improved the way to count assets (images, videos, other) in the export report (rudaporto).
    * When loading data to generate the report now include the full order payload from leica (rudaporto).
    * Include archive and submission folders in the report, counting the number of files in these folders also (rudaporto).
    * Change to use chunks and execute the import orders to alexandria in blocks of ten orders (rudaporto).
    * Change python container to verstion 1.4.5 (rudaporto).
    * Change to use eventlet worker type and add eventlet as dependency (rudaporto).
    * Split workers in three groups and add router rules: default, gdrive, s3 (rudaporto).
    * Added new task to tasks.s3 to download from gdrive and upload to s3 to make sure we will delete the files as soon as possible from /tmp (rudaporto).
    * Added retry exceptions so celery will automatically retry tasks when these errors happen (rudaporto).
    * Added rate limite to tasks that use briefy.gdrive.api calls (rudaporto).
    * Enable retry exponential backoff for tasks that use briefy.gdrive.api (rudaporto).
    * Added also images from sub folders with special names convention when importing assets (rudaporto).
    * Make sure we set a name when a category in the requirement items has no name (rudaporto).
    * Fixing worker names to be stable among restarts when monitoring using celery flower (rudaporto).
    * Check if file exists in S3 before upload again (rudaporto).
    * Added rate limit to kinisis put_record task (rudaporto).
    * Added new tasks to gdrive to find the first user that has permission in a gdrive folder (rudaporto).
    * Fix check permissions to try to add permissions for the folders we have a user with read access (rudaporto).
