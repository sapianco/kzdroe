#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
#
#       kzdroe/kzdroe/s3.py
#       Copyright 2021 sebastian.rojo <sebastian.rojo@sapian.com.co>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#

__author__ = "Sebastian Rojo"
__copyright__ = "Copyright 2020, Sebastian Rojo, Sapian SAS"
__credits__ = []
__license__ = "GPLv2"
__version__ = "0.1.1"
__maintainer__ = "Sebastian Rojo"
__email__ = ["sebastian.rojo at sapian.com.co", "arpagon at gmail.com"]
__status__ = "Beta"

import os
import logging
import boto3
import botocore

LOG_LEVEL = os.environ.get('LOG_LEVEL', "INFO").upper()
S3 = int(os.environ.get('S3', False))
logging.basicConfig(level=LOG_LEVEL)
log = logging.getLogger('KZDROE.S3')

if S3:
    S3_ACCESS_KEY = os.environ.get('S3_ACCESS_KEY', "")
    S3_SECRET_KEY = os.environ.get('S3_SECRET_KEY', "")
    S3_HOST = os.environ.get('S3_HOST', "")

s3 = boto3.client(
        's3',
        endpoint_url=S3_HOST,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        region_name=''
    )

s3_resource = boto3.resource(
        's3',
        endpoint_url=S3_HOST,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        region_name=''
    )


def check_bucket(bucket_name):
    try:
        log.debug("")
        s3_resource.meta.client.head_bucket(Bucket=bucket_name)
        log.debug("Bucket Exists!")
        return True
    except botocore.exceptions.ClientError as e:
        # If a client error is thrown, then check that it was a 404 error.
        # If it was a 404 error, then the bucket does not exist.
        error_code = int(e.response['Error']['Code'])
        if error_code == 403:
            log.debug("Private Bucket. Forbidden Access!")
            return True
        elif error_code == 404:
            log.debug("Bucket Does Not Exist!")
            return False

def upload_file(file_name, bucket_name, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """
    # check if bucket exist
    if not check_bucket(bucket_name):
        s3.create_bucket(Bucket=bucket_name)

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    # Upload the file    
    try:
        response = s3.upload_file(file_name, bucket_name, object_name)
    except botocore.exceptions.ClientError as e:
        log.error(e)
        return False
    return True

if __name__ == '__main__':
    if not (S3_ACCESS_KEY and S3_SECRET_KEY):
        log.error(
            "ERROR: for S3 storage need S3_ACCESS_KEY and S3_SECRET_KEY"
        )
        exit(1)