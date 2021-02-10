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
from flask import Flask
from flask import request
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_flask_exporter.multiprocess import UWsgiPrometheusMetrics
from shutil import copyfile, which
from subprocess import Popen

SOURCE_AUDIO_EXTENSIONS = ['.wav']

LOG_LEVEL = os.environ.get('LOG_LEVEL', "INFO").upper()
METRICS_PORT = int(os.environ.get('METRICS_PORT', "9531"))
ENCOPUS = int(os.environ.get('ENCOPUS', "1"))

logging.basicConfig(level=LOG_LEVEL)
log = logging.getLogger('KZDROE')

app = Flask(__name__)
metrics = UWsgiPrometheusMetrics(app, group_by='endpoint')
metrics.info('app_info', 'Application info', version=__version__)
metrics.register_endpoint('/metrics')
metrics.start_http_server(METRICS_PORT)


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
    dstpath = "tmp/" + accountid + "/" + userid 
    dstfile = dstpath + "/" + recfile
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
        return 'OK {} {}'.format(opusdstfile, request.path)
    else:
        return 'OK {} {}'.format(dstfile, request.path)

if __name__ == '__main__':
    if ENCOPUS:
        if which('opusenc') is None:
            log.error("ERROR: opusenc not found in PATH - please make sure it's installed")
            exit(1)
    metrics.start_http_server(METRICS_PORT)
    app.run(host='0.0.0.0')