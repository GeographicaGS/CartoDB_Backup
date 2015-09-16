# -*- coding: utf-8 -*-
#
#  Author: Cayetano Benavent, 2015.
#  https://github.com/GeographicaGS/CartoDB_Backup
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#

##########################################################################
# Before execute this script you need a cartodbbkconfig.py file properly #
# formed (See cartodbbkconfig_example) in your current/working directory.#
##########################################################################


import argparse
import os
import zipfile
import subprocess
import getpass
import psycopg2
import logging
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import datetime
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.sns import connect_to_region


def runBackup(api_key, cartodb_domain, sql_filedump, pg_backup=False,
                my_database=None, my_user=None, my_password=None,
                my_host=None, my_port=None, new_database=None):
    """
    Backup CartoDB entire domain to SQL dump file. Optionally you can
    restore SQL dumped file to a new (created) PostGIS DB (pg_backup=True)

    """

    logger.info("Start backup process...")

    ogrprm = ['ogr2ogr', '--config', 'PG_USE_COPY', 'YES', '--config',
                'CARTODB_API_KEY', api_key, '-f', 'PGDump', sql_filedump,
                cartodb_domain, '-lco', 'DROP_TABLE=OFF']
    out, err = cmdCall(ogrprm)
    if err:
        logger.error("CartoDB Dump Error: {0}".format(err))
    else:
        logger.info("CartoDB Dump: successfully process!")

    if pg_backup:
        createPostgisDB(my_database, my_password, my_user, my_host, my_port, new_database)

        pgisprm = ['psql', '-h', my_host, '-p', str(my_port), '-d', new_database,
                    '-U', my_user, '-a', '-f', sql_filedump]
        out, err = cmdCall(pgisprm)
        if err:
            logger.error("CartoDB to PostGIS Import Error: {0}".format(err))
        else:
            logger.info("CartoDB to PostGIS Import: successfully process!")


def cmdCall(params):
    """
    Launch shell commands
    """
    try:
        cmd_call = subprocess.Popen(params, stderr=subprocess.PIPE)
        out, err = cmd_call.communicate()
        return(out, err)

    except ValueError as err:
        logger.error("Invalid arguments: {0}".format(err))

    except Exception as err:
        logger.error("Shell command error: {0}".format(err))


def aws_s3storeoutput(filepath, aws_acckey, aws_seckey, aws_bucket, aws_key, validate=False):
    """
    Storing outputs in Amazon S3
    """
    try:
        s3conn = S3Connection(aws_acckey, aws_seckey)
        s3bucket = s3conn.get_bucket(aws_bucket, validate=validate)
        key = "{0}{1}".format(aws_key, os.path.basename(filepath))
        k = Key(s3bucket)
        k.key = key
        k.set_contents_from_filename(filepath)

        logger.info("File successfully uploaded to Amazon S3...")

    except Exception as err:
        logger.error("AWS S3 error: {0}".format(err))


def awsPushSNS(aws_acckey, aws_seckey, sns_arn, sns_regname, message):
    """
    Amazon SNS (Simple Notification Service) reporting
    """
    try:
        if sns_arn and aws_acckey:
            sns = connect_to_region(sns_regname,
                    aws_access_key_id=aws_acckey,
                    aws_secret_access_key=aws_seckey,
                    validate_certs=False)

            sns.publish(sns_arn, message, subject="Finished AWS S3 backup!")
            logger.info("Message successfully sent with AWS SNS...")

        else:
            logger.error("Message not sent with AWS Simple Notification Service...")
            return

    except Exception as err:
        logger.error("AWS SNS error: {0}".format(err))


def createPostgisDB(my_database, my_password, my_user, my_host, my_port,
                    new_database, del_db=True):
    """
    Create new PostGIS database to store sql dumped file previously

    """

    logger.info("PostGIS: creating DB...")

    try:
        conn = None
        conn = psycopg2.connect(database=my_database, user=my_user,
        password=my_password, host=my_host, port=my_port)

        # Conection to create new database
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        if del_db:
            cur.execute("DROP DATABASE IF EXISTS {0};".format(new_database))
            logger.info("Database {0} removed".format(new_database))

        cur.execute("CREATE DATABASE {0};".format(new_database))
        cur.close()
        conn.close()
        logger.info("Database {0} created".format(new_database))

        # New conection to new_database
        conn = psycopg2.connect(database=new_database, user=my_user,
        password=my_password, host=my_host, port=my_port)
        cur = conn.cursor()
        cur.execute("CREATE EXTENSION postgis;")
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Added PostGIS extension to {0}".format(new_database))

    except Exception as err:
        logger.error("Database creation error: {0}".format(err))


def getPsw(my_user):
    """
    Get password from shell
    """
    msg = "Enter password for user {0}: ".format(my_user)
    return getpass.getpass(msg)


def zipSql(sqlfolder, flname):
    """
    Zip sql dump file
    """
    try:
        zipflname = os.path.join(sqlfolder, "{0}.zip".format(os.path.splitext(flname)[0]))

        with zipfile.ZipFile(zipflname,'w',zipfile.ZIP_DEFLATED) as zfl:
            zfl.write(os.path.join(sqlfolder, flname), flname)

        logger.info("SQL file compressed: {}".format(zipflname))

        return(zipflname)

    except Exception as err:
        logger.error("Zip compression error: {0}".format(err))


def rmvSqlFile(sqlfilepath):
    """
    Remove sql dump file after compression
    """

    try:
        os.remove(sqlfilepath)

    except Exception as err:
        logger.error("Error removing sql file: {0}".format(err))


def main():
    
    cfg_msg = """
    -----------------------------------------
        Before execute this script you need a
        cartodbbkconfig.py file properly
        formed (See cartodbbkconfig_example)
        in your current/working directory.
    -----------------------------------------"""
    try:
        from cartodbbkconfig import confparams

    except ImportError as err:
        logger.error("{0}Error: {1}".format(cfg_msg, err))
        raise SystemExit()

    except Exception as err:
        logger.error("{0}Error: {1}".format(cfg_msg, err))
        raise SystemExit()

    descr = """Backup CartoDB entire domain to SQL dump file. Optionally you can
                restore SQL dumped file to a new (created) PostGIS DB"""
    arg_parser = argparse.ArgumentParser(description=descr)

    arg_parser.add_argument('--postgis_backup', help='PostGIS backup (restoring dump file created)',
                            action="store_true")

    arg_parser.add_argument('--aws_s3upload', help='Upload file to Amazon S3',
                            action="store_true")

    arg_parser.add_argument('--amz_sns', help='Amazon SNS message',
                            action="store_true")

    args = arg_parser.parse_args()

    postgis_backup = args.postgis_backup
    aws_s3upload = args.aws_s3upload
    amz_sns = args.amz_sns

    API_KEY = confparams.get("cdb_apikey")
    cartodb_domain = 'CartoDB:{}'.format(confparams.get("cdb_domain"))
    sql_folderdump = confparams.get("sql_folderpath")
    dt_now = datetime.now().strftime("%Y%m%d_%H%M%S")
    bk_file = "cartodb_backup_{0}.sql".format(dt_now)
    sql_filepath = os.path.join(sql_folderdump, bk_file)

    if postgis_backup:
        my_database = confparams.get("pg_dbase")
        my_user = confparams.get("pg_user")
        my_host = confparams.get("pg_host")
        my_port = confparams.get("pg_port")
        new_database = "{0}_{1}".format(confparams.get("pg_newdatabase"), dt_now)

        my_password = confparams["pg_pswd"]
        if not my_password:
            my_password = getPsw(my_user)

        runBackup(API_KEY, cartodb_domain, sql_filepath, pg_backup=True,
                my_database=my_database, my_user=my_user, my_password=my_password,
                my_host=my_host, my_port=my_port, new_database=new_database)
    else:
        runBackup(API_KEY, cartodb_domain, sql_filepath)

    zpfile = zipSql(sql_folderdump, bk_file)
    rmvSqlFile(sql_filepath)

    if aws_s3upload:
        aws_acckey = confparams.get("aws_acckey")
        aws_seckey = confparams.get("aws_seckey")
        aws_bucket = confparams.get("aws_bucket")
        aws_key = confparams.get("aws_key")
        aws_s3storeoutput(zpfile, aws_acckey, aws_seckey, aws_bucket, aws_key)

        if amz_sns:
            sns_arn = confparams.get("sns_arn")
            sns_regname = confparams.get("sns_regname")
            lg = ["[{0} {1}] - {2}".format(i.asctime, i.levelname, i.message) for i in mh.buffer]
            message = "\n".join(lg)
            awsPushSNS(aws_acckey, aws_seckey, sns_arn, sns_regname, message)


if __name__ == '__main__':

    logfmt = "[%(asctime)s - %(levelname)s] - %(message)s"
    dtfmt = "%Y-%m-%d %I:%M:%S"
    logging.basicConfig(level=logging.INFO, format=logfmt, datefmt=dtfmt)

    mh = logging.handlers.MemoryHandler(0)
    mh.setLevel(logging.INFO)
    mh.setFormatter(logging.Formatter(logfmt))

    logger = logging.getLogger()
    logger.addHandler(mh)

    main()
