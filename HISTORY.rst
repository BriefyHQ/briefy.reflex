=======
History
=======

0.1.0 (Unreleased)
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
