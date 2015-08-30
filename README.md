# CartoDB Backup
Python CLI to make a backup of an entire CartoDB domain to SQL dump file.
Optionally you can restore SQL dumped file to a new (created) PostGIS DB.

Before execute this script you need a cartodbbkconfig file properly
formed (See cartodbbkconfig_example) in your current/working directory.

This script is

```python
confparams = {
                "cdb_apikey": "here your api key",
                "cdb_domain": "here your domain"
                "sql_folderpath": "here your dump folderpath",
                "pg_user": "here your db admin user",
                "pg_pswd": None, # If you leave the password to None, the program will ask you in the command line interface
                "pg_dbase": "here your db name",
                "pg_host": "here your db host",
                "pg_port": "here your db port",
                "pg_newdatabase": "here your new db name"
            }
```

## Usage
Python CLI:

```bash
$ python cartodb_backup.py [-h] [--postgis_backup POSTGIS_BACKUP]

optional arguments:
  -h, --help            show this help message and exit
  --postgis_backup      POSTGIS_BACKUP PostGIS backup (restoring dump file created)

```
Example without PostGIS backup:
```bash
$ python cartodb_backup.py

```
Example with PostGIS backup:
```bash
$ python cartodb_backup.py --postgis_backup

```

## Requirements
- GDAL (>= 1.11).
- PostgreSQL with PostGIS (1).
- Psycopg2 Python library (1).

(1) Only if you want to use --postgis_backup parameter.

## About author
Developed by Cayetano Benavent.
GIS Analyst at Geographica.

http://www.geographica.gs


## License
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
