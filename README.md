# CartoDB Backup
Backup CartoDB entire domain to SQL dump file. Optionally you can restore SQL
dumped file to a new (created) PostGIS DB.

Before execute this script you need a cartodbbkconfig file properly
formed (See cartodbbkconfig_example) in your current/working directory.

```python
confparams = {
                "cdb_apikey": "here your api key",
                "cdb_domain": "here your domain"
                "sql_filedump": "here your dump filepath",
                "pg_user": "here your db admin user",
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
