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
from datetime import datetime
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def runBackup(API_KEY, cartodb_domain, sql_filedump, pg_backup=False,
                my_database=None, my_user=None, my_password=None,
                my_host=None, my_port=None, new_database=None):
    """
    Backup CartoDB entire domain to SQL dump file. Optionally you can
    restore SQL dumped file to a new (created) PostGIS DB (pg_backup=True)

    """
    try:

        print("\nStart backup process..")

        cdb_dmp = subprocess.Popen(['ogr2ogr', '--config', 'PG_USE_COPY', 'YES',
                                    '--config', 'CARTODB_API_KEY', API_KEY, '-f',
                                    'PGDump', sql_filedump, cartodb_domain, '-lco',
                                    'DROP_TABLE=OFF'], stderr=subprocess.PIPE)

        out, err = cdb_dmp.communicate()
        if err:
            print("\nCartoDB Dump Error:", err)
        else:
            print("\nCartoDB Dump: successfully process!")

        if pg_backup:
            createPostgisDB(my_database, my_password, my_user, my_host, my_port, new_database)

            cdb_pgis = subprocess.Popen(['psql', '-h', my_host, '-p', str(my_port),
                                        '-d', new_database, '-U', my_user, '-a',
                                        '-f', sql_filedump], stderr=subprocess.PIPE)

            out, err = cdb_pgis.communicate()
            if err:
                print("\nCartoDB to PostGIS Import Error:", err)
            else:
                print("\nCartoDB to PostGIS Import: successfully process!")

    except Exception as err:
        print("Error:", err)


def createPostgisDB(my_database, my_password, my_user, my_host, my_port, new_database):
    """
    Create new PostGIS database to store sql dumped file previously

    """

    print("PostGIS: creating DB...")

    try:
        conn = None
        conn = psycopg2.connect(database=my_database, user=my_user,
        password=my_password, host=my_host, port=my_port)

        # Conection to postgres_database
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        # cur.execute("DROP DATABASE {0};".format(new_database))
        cur.execute("CREATE DATABASE {0};".format(new_database))
        cur.close()
        conn.close()
        print("Database {0} created".format(new_database))

        # New conection to new_database
        conn = psycopg2.connect(database=new_database, user=my_user,
        password=my_password, host=my_host, port=my_port)
        cur = conn.cursor()
        cur.execute("CREATE EXTENSION postgis;")
        conn.commit()
        cur.close()
        conn.close()
        print("Added PostGIS extension to {0}".format(new_database))

    except Exception as err:
        print(err)


def getPsw(my_user):
    """
    Get password from shell
    """
    msg = "Enter password for user {}: ".format(my_user)
    return getpass.getpass(msg)


def zipSql(sqlfolder, flname):
    """
    Zip sql dump file
    """
    try:
        zipflname = os.path.join(sqlfolder, "{0}.zip".format(os.path.splitext(flname)[0]))

        with zipfile.ZipFile(zipflname,'w',zipfile.ZIP_DEFLATED) as zfl:
            zfl.write(os.path.join(sqlfolder, flname), flname)

        print("sql file compressed: {}".format(zipflname))

    except Exception as err:
        print(err)


def rmvSqlFile(sqlfilepath):
    """
    Remove sql dump file after compression
    """

    try:
        os.remove(sqlfilepath)

    except Exception as err:
        print(err)


def main():

    cfg_msg = """
    -----------------------------------------
        Before execute this script you need a
        cartodbbkconfig.py file properly
        formed (See cartodbbkconfig_example)
        in your current/working directory.
    -----------------------------------------\n"""
    try:
        from cartodbbkconfig import confparams

    except ImportError as err:
        print("{0}Error: {1}".format(cfg_msg, err))
        raise SystemExit()

    except Exception as err:
        print("{0}Error: {1}\n".format(cfg_msg, err))
        raise SystemExit()


    descr = """Backup CartoDB entire domain to SQL dump file. Optionally you can
                restore SQL dumped file to a new (created) PostGIS DB"""
    arg_parser = argparse.ArgumentParser(description=descr)

    arg_parser.add_argument('--postgis_backup', help='PostGIS backup (restoring dump file created)',
                            action="store_true")

    args = arg_parser.parse_args()

    postgis_backup = args.postgis_backup

    API_KEY = confparams["cdb_apikey"]
    cartodb_domain = 'CartoDB:{}'.format(confparams["cdb_domain"])
    sql_folderdump = confparams["sql_folderpath"]
    bk_file = "cartodb_backup_{0}.sql".format(datetime.now().strftime("%Y%m%d_%H%M%S"))
    sql_filepath = os.path.join(sql_folderdump, bk_file)

    if postgis_backup:
        my_database = confparams["pg_dbase"]
        my_user = confparams["pg_user"]
        my_host = confparams["pg_host"]
        my_port = confparams["pg_port"]
        new_database = confparams["pg_newdatabase"]
        my_password = confparams["pg_pswd"]
        if not my_password:
            my_password = getPsw(my_user)

        runBackup(API_KEY, cartodb_domain, sql_filepath, pg_backup=True,
                my_database=my_database, my_user=my_user, my_password=my_password,
                my_host=my_host, my_port=my_port, new_database=new_database)
    else:
        runBackup(API_KEY, cartodb_domain, sql_filepath)

    zipSql(sql_folderdump, bk_file)
    rmvSqlFile(sql_filepath)

if __name__ == '__main__':
    main()
