#  Copyright (c) 2015 SONATA-NFV, 5GTANGO, UBIWHERE, Paderborn University
# ALL RIGHTS RESERVED.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Neither the name of the SONATA-NFV, 5GTANGO, UBIWHERE, Paderborn University
# nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written
# permission.
#
# This work has been performed in the framework of the SONATA project,
# funded by the European Commission under Grant number 671517 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.sonata-nfv.eu).
#
# This work has also been performed in the framework of the 5GTANGO project,
# funded by the European Commission under Grant number 761493 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.5gtango.eu).

import logging
import subprocess
import os
from flask import Flask, Blueprint
from flask_restplus import Resource, Api, Namespace
from werkzeug.contrib.fixers import ProxyFix


log = logging.getLogger(__name__)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
blueprint = Blueprint('api', __name__, url_prefix="/api")
api_v1 = Namespace("v1", description="tng-project API v1")
api = Api(blueprint, version="0.1", title='5GTANGO tng-project API',
          description="5GTANGO tng-project REST API for project management.")
app.register_blueprint(blueprint)
api.add_namespace(api_v1)


# parser arguments: for input parameters sent to the API
# TODO: parser arguments

# models for marshaling return values from the API
# TODO: models (better to use marshmallow here?)

# TODO: dump swagger

# start REST API server
def serve_forever(args, debug=True):
    # TODO replace this with WSGIServer for better performance
    app.cliargs = args
    app.run(host=args.service_address, port=args.service_port, debug=debug)


@api_v1.route("/pings")
class Ping(Resource):
    # @api_v1.marshal_with(ping_get_return_model)
    def get(self):
        ut = None
        try:
            ut = str(subprocess.check_output("uptime")).strip()
        except BaseException as e:
            log.warning(str(e))
        return {"alive_since": ut}
