# CartoDB Backup
Python CLI to make a backup of an entire CartoDB domain to SQL dump file (zipped).

Optional:
- You can restore SQL dumped file to a new (created) PostGIS DB.
- You can upload sql files to Amazon S3.
- Message from Amazon SNS (Simple Notification Service).

Before execute this script you need a cartodbbkconfig.py file properly
formed (See cartodbbkconfig_example.py) in your current/working directory.
This file (cartodbbkconfig.py) must be in ".gitignore".

cartodbbkconfig.py config parameters:

```python
confparams = {
                "cdb_apikey": "here your api key",
                "cdb_domain": "here your domain",
                "sql_folderpath": "here your dump folderpath",
                "pg_user": "here your db admin user",
                "pg_pswd": None, # If you leave the password to None, the program will ask you in the command line interface
                "pg_dbase": "here your db name",
                "pg_host": "here your db host",
                "pg_port": "here your db port",
                "pg_newdatabase": "here your new db name",
                "aws_acckey": "here your AWS Acces Key",
                "aws_seckey": "here your AWS Secret Key",
                "aws_bucket": "here your AWS bucket",
                "aws_prekey": "here your AWS bucket prefix key",
                "sns_regname": "here your AWS region name",
                "sns_arn": "here your SNS ARN",
                "sns_subject": "My project"
            }
```

## Usage
Python CLI:

```bash
$ python cartodb_backup.py [-h] [--postgis_backup] [--aws_s3upload] [--amz_sns]

optional arguments:
  -h, --help            show this help message and exit
  --postgis_backup      POSTGIS_BACKUP PostGIS backup (restoring dump file created)
  --aws_s3upload        Upload file to Amazon S3
  --amz_sns             Amazon SNS message

```
Example without PostGIS backup:
```bash
$ python cartodb_backup.py

```
Example with PostGIS backup:
```bash
$ python cartodb_backup.py --postgis_backup

```
Example with Amazon S3 upload:
```bash
$ python cartodb_backup.py --aws_s3upload

```
Example with Amazon S3 upload and Amazon SNS:
```bash
$ python cartodb_backup.py --aws_s3upload --amz_sns

```

## Requirements
- GDAL >= 1.11.
- PostgreSQL with PostGIS (1).
- Psycopg2 Python library (1).
- Python interface to Amazon Web Services (Boto) (2).

(1) Only if you want to use --postgis_backup parameter.
(2) Only if you want to use --aws_s3upload parameter.

## About author
Developed by Cayetano Benavent.
GIS Analyst at Geographica.

http://www.geographica.gs


## License
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
