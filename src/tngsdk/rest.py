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
import json
import os
import uuid
from flask import Flask, Blueprint
from flask_restplus import Resource, Api, Namespace
from werkzeug.contrib.fixers import ProxyFix
import tngsdk.project.project as cli


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
# parser = api_v1.parser()
# parser.add_argument("filename",
#                     location="form",
#                     required=True,
#                     help="Project name (no whitespaces)")
# TODO: make optional and create projects using uuid

# models for marshaling return values from the API
# TODO: models (better to use marshmallow here?)


def dump_swagger():
    # TODO replace this with the URL of a real tng-project service
    app.config.update(SERVER_NAME="tng-project.5gtango.eu")
    with app.app_context():
        with open(os.path.join("docs", "rest_api.json"), "w") as f:
            f.write(json.dumps(api.__schema__))


# start REST API server
def serve_forever(args, debug=True):
    # TODO replace this with WSGIServer for better performance
    log.info("Starting tng-project in service mode")
    app.cliargs = args
    app.run(host=args.service_address, port=args.service_port, debug=debug)


@api_v1.route("/pings")
class Ping(Resource):
    def get(self):
        ut = None
        try:
            ut = str(subprocess.check_output("uptime")).strip()
        except BaseException as e:
            log.warning(str(e))
        return {"alive_since": ut}


@api_v1.route("/projects")
class Projects(Resource):
    def get(self):
        log.info("GET to /projects. Loading available projects")
        project_dirs = [name for name in os.listdir('projects') if os.path.isdir(os.path.join('projects', name))]
        return {'projects': project_dirs}
    # TODO: check UUID in project manifest? should be consistent to project dir name anyways

    def post(self):
        # args = parser.parse_args()
        log.info("POST to /projects")
        new_uuid = str(uuid.uuid4())
        cli_args, extra_ars = cli.parse_args_project([
            '-p', os.path.join('projects', new_uuid)
        ])
        project = cli.create_project(cli_args, extra_ars, fixed_uuid=new_uuid)

        return {'uuid': project.uuid}

