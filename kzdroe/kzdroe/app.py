#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
#
#       kzdroe/kzdroe/app.py
#       Copyright 2020 sebastian.rojo <sebastian.rojo@sapian.com.co>
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
from datetime import datetime
from flask import Flask
from flask import request
from flask import jsonify
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_flask_exporter.multiprocess import UWsgiPrometheusMetrics
from shutil import copyfile, which
from subprocess import Popen

SOURCE_AUDIO_EXTENSIONS = ['.wav']
GREGORIAN_SECONDS=62167219200
LOG_LEVEL = os.environ.get('LOG_LEVEL', "INFO").upper()
METRICS_PORT = int(os.environ.get('METRICS_PORT', "9531"))
ENCOPUS = int(os.environ.get('ENCOPUS', True))
S3 = int(os.environ.get('S3', False))

logging.basicConfig(level=LOG_LEVEL)
log = logging.getLogger('KZDROE')

app = Flask(__name__)
metrics = UWsgiPrometheusMetrics(app, group_by='endpoint')
metrics.info('app_info', 'Application info', version=__version__)
metrics.register_endpoint('/metrics')
metrics.start_http_server(METRICS_PORT)

if S3:
    from kzdroe.s3 import upload_file

@app.route('/ping', methods=['GET'])
def ping():
    return 'Pong', 200

@app.route('/kzr/<accountid>/<userid>/<recfile>', methods=['PUT'])
@metrics.counter(
    'cnt_accountid', 'Number of invocations per accountid', labels={
        'accountid': lambda: request.view_args['accountid'],
        'status': lambda resp: resp.status_code
    })
@metrics.counter(
    'cnt_userid', 'Number of invocations per userid', labels={
        'userid': lambda: request.view_args['userid'],
        'status': lambda resp: resp.status_code
    })
def upload(accountid, userid, recfile):
    result={}
    now_greg_timestamp = datetime.now().timestamp() + GREGORIAN_SECONDS
    start_greg_timestamp = request.args.get(
        'start', 
        default = now_greg_timestamp, 
        type = int
    )
    result['start_greg_timestamp']=start_greg_timestamp
    calldatetime=datetime.fromtimestamp(
        start_greg_timestamp - GREGORIAN_SECONDS
    )
    result['calldatetime']=calldatetime
    dstpath = (
        "rec/" + 
        accountid + 
        "/" + 
        userid + 
        calldatetime.strftime("/%Y/%m/%d/%H")
    )
    dstfile = dstpath + "/" + recfile
    result['srcfile']=recfile
    result['dstfile']=dstfile
    if not os.path.exists(dstpath):
        os.makedirs(dstpath)
    with open(dstfile, 'wb') as f:
        print(dir(request))
        f.write(request.data)
    if ENCOPUS:
        opusdstfile = os.path.splitext(dstfile)[0] + ".opus"
        log.info(
            'running: opusenc --speech {} {}'.format(
                dstfile, 
                opusdstfile
            )
        )
        if Popen(
            [
                'opusenc',
                '--speech', 
                dstfile, 
                opusdstfile 
            ]).wait() == 0:
            log.info(
                'converted {} -> {}'.format(
                    dstfile, 
                    opusdstfile
                )
            )
            finalfile=opusdstfile
            result["opusfile"]=opusdstfile
            result["finalfile"]=opusdstfile
            result['opus_transcode']=True
    else:
        finalfile=dstfile
        result["finalfile"]=dstfile
        result['opus_transcode']=False
    if S3:
        if upload_file(finalfile,accountid):
            result["s3_key"]="s3://" + accountid + "/" + finalfile
            result["s3_upload"]=True
        else:
            result["s3_upload"]=False
    return jsonify(result)

if __name__ == '__main__':
    if not (S3_ACCESS_KEY and S3_SECRET_KEY):
        log.error(
            "ERROR: for S3 storage need S3_ACCESS_KEY and S3_SECRET_KEY"
        )
        exit(1)
    if ENCOPUS:
        if which('opusenc') is None:
            log.error("ERROR: opusenc not found in PATH - please make sure it's installed")
            exit(1)
    metrics.start_http_server(METRICS_PORT)
    app.run(host='0.0.0.0')