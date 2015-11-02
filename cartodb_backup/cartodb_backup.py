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



import os
import zipfile
import subprocess
import getpass
import psycopg2
import logging
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.sns import connect_to_region



class CartoDBBackup(object):

    def __init__(self, api_key, cartodb_domain):
        """
        api_key: CartoDB API key
        cartodb_domain: CartoDB domain

        """
        self.__api_key = api_key
        self.__cartodb_domain = cartodb_domain
        self.__logger, self.__mh = self.__logHandler()


    def __logHandler(self):
        """
        Log handler
        """
        logfmt = "[%(asctime)s - %(levelname)s] - %(message)s"
        dtfmt = "%Y-%m-%d %I:%M:%S"
        logging.basicConfig(level=logging.INFO, format=logfmt, datefmt=dtfmt)

        mh = logging.handlers.MemoryHandler(0)
        mh.setLevel(logging.INFO)
        mh.setFormatter(logging.Formatter(logfmt))

        logger = logging.getLogger()
        logger.addHandler(mh)

        return(logger, mh)


    def runBackup(self, sql_filedump, pg_backup=False, my_database=None,
                    my_user=None, my_password=None, my_host=None, my_port=None,
                    new_database=None):
        """
        Backup CartoDB entire domain to SQL dump file. Optionally you can
        restore SQL dumped file to a new (created) PostGIS DB (pg_backup=True)

        """
        try:
            self.__logger.info("Start backup process...")

            ogrprm = ['ogr2ogr', '--config', 'PG_USE_COPY', 'YES', '--config',
                        'CARTODB_API_KEY', self.__api_key, '-f', 'PGDump',
                        sql_filedump, self.__cartodb_domain, '-lco', 'DROP_TABLE=OFF']

            out, err = self.__cmdCall(ogrprm)

            if err:
                self.__logger.error("CartoDB Dump Error: {0}".format(err))
            else:
                self.__logger.info("CartoDB Dump: successfully process!")

        except Exception as err:
            self.__logger.error("Check your GDAL >=1.11 installation: {0}".format(err))

        if pg_backup:
            self.__createPostgisDB(my_database, my_password, my_user, my_host, my_port, new_database)

            try:
                pgisprm = ['psql', '-h', my_host, '-p', str(my_port), '-d', new_database,
                            '-U', my_user, '-a', '-f', sql_filedump]
                out, err = self.__cmdCall(pgisprm)
                if err:
                    self.__logger.error("CartoDB to PostGIS Import Error: {0}".format(err))
                else:
                    self.__logger.info("CartoDB to PostGIS Import: successfully process!")

            except Exception as err:
                self.__logger.error("Check your postgresql-client installation: {0}".format(err))


    def __cmdCall(self, params):
        """
        Launch shell commands
        """
        try:
            cmd_call = subprocess.Popen(params, stderr=subprocess.PIPE)
            out, err = cmd_call.communicate()
            return(out, err)

        except ValueError as err:
            self.__logger.error("Invalid arguments: {0}".format(err))

        except Exception as err:
            self.__logger.error("Shell command error: {0}".format(err))


    def awsS3StoreOutput(self, filepath, aws_acckey, aws_seckey, aws_bucket,
                            aws_prekey, validate=False, rmvfl=False):
        """
        Storing outputs in Amazon S3

        """
        try:
            s3conn = S3Connection(aws_acckey, aws_seckey)
            s3bucket = s3conn.get_bucket(aws_bucket, validate=validate)
            key = "{0}{1}".format(aws_prekey, os.path.basename(filepath))
            k = Key(s3bucket)
            k.key = key
            k.set_contents_from_filename(filepath)

            self.__logger.info("File successfully uploaded to Amazon S3...")

            if rmvfl:
                self.rmvSqlFile(filepath, lg=True)


        except Exception as err:
            self.__logger.error("AWS S3 error: {0}".format(err))


    def awsPushSNS(self, aws_acckey, aws_seckey, sns_arn, sns_regname, sbj=None):
        """
        Amazon SNS (Simple Notification Service) reporting
        """
        try:
            if sns_arn and aws_acckey:
                sns = connect_to_region(sns_regname,
                        aws_access_key_id=aws_acckey,
                        aws_secret_access_key=aws_seckey,
                        validate_certs=False)

                if sbj:
                    subject = "{0} - Finished AWS S3 backup!".format(sbj)
                else:
                    subject = "Finished AWS S3 backup!"

                lg = ["[{0} {1}] - {2}".format(i.asctime, i.levelname, i.message) for i in self.__mh.buffer]
                message = "\n".join(lg)

                sns.publish(sns_arn, message, subject=subject)
                self.__logger.info("Message successfully sent with AWS SNS...")

            else:
                self.__logger.error("Message not sent with AWS Simple Notification Service...")
                return

        except Exception as err:
            self.__logger.error("AWS SNS error: {0}".format(err))


    def __createPostgisDB(self, my_database, my_password, my_user, my_host,
                            my_port, new_database, del_db=True):
        """
        Create new PostGIS database to store sql dumped file previously

        """

        self.__logger.info("PostGIS: creating DB...")

        try:
            conn = None
            conn = psycopg2.connect(database=my_database, user=my_user,
                    password=my_password, host=my_host, port=my_port)

            # Conection to create new database
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()

            if del_db:
                cur.execute("DROP DATABASE IF EXISTS {0};".format(new_database))
                self.__logger.info("Database {0} removed".format(new_database))

            cur.execute("CREATE DATABASE {0};".format(new_database))
            cur.close()
            conn.close()
            self.__logger.info("Database {0} created".format(new_database))

            # New conection to new_database
            conn = psycopg2.connect(database=new_database, user=my_user,
            password=my_password, host=my_host, port=my_port)
            cur = conn.cursor()
            cur.execute("CREATE EXTENSION postgis;")
            conn.commit()
            cur.close()
            conn.close()
            self.__logger.info("Added PostGIS extension to {0}".format(new_database))

        except Exception as err:
            self.__logger.error("Database creation error: {0}".format(err))


    def getPsw(self, my_user):
        """
        Get password from shell
        """
        msg = "Enter password for user {0}: ".format(my_user)
        return getpass.getpass(msg)


    def zipSql(self, sqlfolder, flname):
        """
        Zip sql dump file
        """
        try:
            zipflname = os.path.join(sqlfolder, "{0}.zip".format(os.path.splitext(flname)[0]))

            with zipfile.ZipFile(zipflname,'w',zipfile.ZIP_DEFLATED) as zfl:
                zfl.write(os.path.join(sqlfolder, flname), flname)

            self.__logger.info("SQL file compressed: {}".format(zipflname))

            return(zipflname)

        except Exception as err:
            self.__logger.error("Zip compression error: {0}".format(err))


    def rmvSqlFile(self, filepath, lg=False):
        """
        Remove sql dump file after compression
        and after a successfully amazon S3 upload
        """

        try:
            os.remove(filepath)

            if lg:
                self.__logger.info("SQL file successfully removed from local folder...")

        except Exception as err:
            self.__logger.error("Error removing sql file: {0}".format(err))
