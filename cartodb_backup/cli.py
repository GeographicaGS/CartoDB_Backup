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
# formed (See cartodbbkconfig_example).                                  #
##########################################################################


import os
import sys
import argparse
from datetime import datetime
from cartodb_backup import CartoDBBackup



def run():

    descr = """Backup CartoDB entire domain to SQL dump file. Optionally you can
                restore SQL dumped file to a new (created) PostGIS DB.
                You can upload sql files to Amazon S3."""

    cfg_msg = """
    -----------------------------------------
        Before execute this script you need a
        cartodbbkconfig.py file properly
        formed (See cartodbbkconfig_example).
    -----------------------------------------\n"""

    arg_parser = argparse.ArgumentParser(description=descr)

    arg_parser.add_argument('configfile', type=str, help='Config filepath: /locationfolder/')

    arg_parser.add_argument('--postgis_backup', help='PostGIS backup (restoring dump file created)',
                            action="store_true")

    arg_parser.add_argument('--aws_s3upload', help='Upload file to Amazon S3',
                            action="store_true")

    arg_parser.add_argument('--amz_sns', help='Amazon SNS message',
                            action="store_true")

    arg_parser.add_argument('--rmv_localfl', help='Remove local file after a successfully Amazon S3 upload',
                            action="store_true")

    args = arg_parser.parse_args()

    configfile = args.configfile
    postgis_backup = args.postgis_backup
    aws_s3upload = args.aws_s3upload
    amz_sns = args.amz_sns
    rmv_localfl = args.rmv_localfl

    try:
        sys.path.append(configfile)

        from cartodbbkconfig import confparams

    except ImportError as err:
        print("{0}Error: {1}".format(cfg_msg, err))
        raise SystemExit()

    except Exception as err:
        print("{0}Error: {1}".format(cfg_msg, err))
        raise SystemExit()


    api_key = confparams.get("cdb_apikey")
    cartodb_domain = 'CartoDB:{}'.format(confparams.get("cdb_domain"))
    sql_folderdump = confparams.get("sql_folderpath")
    dt_now = datetime.now().strftime("%Y%m%d_%H%M%S")
    bk_file = "cartodb_backup_{0}.sql".format(dt_now)
    sql_filepath = os.path.join(sql_folderdump, bk_file)

    cdb_bk = CartoDBBackup(api_key, cartodb_domain)

    if postgis_backup:
        my_database = confparams.get("pg_dbase")
        my_user = confparams.get("pg_user")
        my_host = confparams.get("pg_host")
        my_port = confparams.get("pg_port")
        new_database = "{0}_{1}".format(confparams.get("pg_newdatabase"), dt_now)

        my_password = confparams.get("pg_pswd")
        if not my_password:
            my_password = cdb_bk.getPsw(my_user)

        cdb_bk.runBackup(sql_filepath, pg_backup=True, my_database=my_database,
                            my_user=my_user, my_password=my_password, my_host=my_host,
                            my_port=my_port, new_database=new_database)
    else:
        cdb_bk.runBackup(sql_filepath)

    zpfile = cdb_bk.zipSql(sql_folderdump, bk_file)
    cdb_bk.rmvSqlFile(sql_filepath)

    if aws_s3upload:
        aws_acckey = confparams.get("aws_acckey")
        aws_seckey = confparams.get("aws_seckey")
        aws_bucket = confparams.get("aws_bucket")
        aws_prekey = confparams.get("aws_prekey")

        rmvfl = False
        if rmv_localfl:
            rmvfl = True

        cdb_bk.awsS3StoreOutput(zpfile, aws_acckey, aws_seckey, aws_bucket,
                                    aws_prekey, rmvfl=rmvfl)

        if amz_sns:
            sns_arn = confparams.get("sns_arn")
            sns_regname = confparams.get("sns_regname")
            sns_subject = confparams.get("sns_subject")

            cdb_bk.awsPushSNS(aws_acckey, aws_seckey, sns_arn, sns_regname, sbj=sns_subject)
