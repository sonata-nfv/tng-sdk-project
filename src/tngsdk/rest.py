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
import shutil
import zipfile
from flask import Flask, Blueprint, send_from_directory
from flask_restplus import Resource, Api, Namespace, fields, inputs
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.datastructures import FileStorage
from tngsdk import cli
# important: import as cli_project; else would collide with Project class here
from tngsdk.project.project import Project as cli_project
from flask_cors import CORS
from os import listdir
from os.path import isfile, join
import ntpath

log = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
app.wsgi_app = ProxyFix(app.wsgi_app)
blueprint = Blueprint('api', __name__, url_prefix="/api")
api_v1 = Namespace("v1", description="tng-project API v1")
api = Api(blueprint, version="0.1", title='5GTANGO tng-project API',
          description="5GTANGO tng-project REST API for project management.")
app.register_blueprint(blueprint)
api.add_namespace(api_v1)


# parser arguments: for input parameters sent to the API
project_parser = api_v1.parser()
project_parser.add_argument("author",
                            required=False,
                            default='eu.tango',
                            help="Service author")
project_parser.add_argument("vendor",
                            required=False,
                            default='eu.tango',
                            help="Service vendor")
project_parser.add_argument("name",
                            required=False,
                            default='example-service',
                            help="Service name")
project_parser.add_argument("description",
                            required=False,
                            default='Example description',
                            help="Service description")
project_parser.add_argument("vnfs",
                            type=int,
                            required=False,
                            default=1,
                            help="Number of VNFs in the service")
project_parser.add_argument("image_names",
                            type=str,
                            required=False,
                            help="List of VNF image names (space-separated)")
project_parser.add_argument("image_types",
                            type=str,
                            required=False,
                            help="List of VNF image types (space-separated)")
project_parser.add_argument("only_tango",
                            # do not use "bool"!
                            # https://github.com/noirbizarre/flask-restplus/issues/199#issuecomment-276645303
                            type=inputs.boolean,
                            required=False,
                            default=False,
                            help="Generate only 5GTANGO descriptors")
project_parser.add_argument("only_osm",
                            type=inputs.boolean,
                            required=False,
                            default=False,
                            help="Generate only OSM descriptors")

file_upload_parser = api_v1.parser()
file_upload_parser.add_argument("file",
                                location="files",
                                type=FileStorage,
                                required=True,
                                help="Uploaded file to add to project")
file_upload_parser.add_argument("file_type",
                                required=False,
                                default=None,
                                help="MIME type of an uploaded file")

filename_parser = api_v1.parser()
filename_parser.add_argument("filename", required=True, help="Filename of the file to remove")

package_parser = api_v1.parser()
package_parser.add_argument("skip_validation", required=False, type=inputs.boolean, default=False,
                            help="If true, skip validation when packaging. Else validate first.")

# models for marshaling return values from the API (also used for generating Swagger spec)
ping_get_model = api_v1.model("PingGet", {
    "alive_since": fields.String(description="system uptime", required=True)
})
projects_get_model = api_v1.model("ProjectsGet", {
    "projects": fields.List(fields.String, description="list of all project UUIDs", required=True)
})
projects_post_model = api_v1.model("ProjectsPost", {
    "uuid": fields.String(description="project UUID", required=True),
    "error_msg": fields.String(description="error message"),
    "files": fields.List(fields.String, description="list of files along with access points", required=True)
})
project_get_model = api_v1.model("ProjectGet", {
    "project_uuid": fields.String(description="project UUID", required=True),
    "manifest": fields.String(description="project manifest", required=True),
    "error_msg": fields.String(description="error message", required=True),
})
project_delete_model = api_v1.model("ProjectDelete", {
    "project_uuid": fields.String(description="project UUID", required=True)
})
# model per file used for nested files type
file_model = api_v1.model("File", {
    'path': fields.String(attribute='path'),
    'type': fields.String(attribute='type'),
    'tags': fields.List(fields.String)
})
files_get_model = api_v1.model("FilesGet", {
    "project_uuid": fields.String(description="project UUID"),
    "files": fields.List(fields.Nested(api_v1.models['File']), description="list of all project files"),
    "error_msg": fields.String(description="error message")
})
files_post_model = api_v1.model("FilesPost", {
    "project_uuid": fields.String(description="project UUID"),
    "filename": fields.String(description="added file"),
    "error_msg": fields.String(description="error message")
})
files_delete_model = api_v1.model("FilesDelete", {
    "project_uuid": fields.String(description="project UUID"),
    "removed_file": fields.String(description="deleted file"),
    "error_msg": fields.String(description="error message")
})

package_post_model = api_v1.model("PackagePost", {
    "project_uuid": fields.String(description="Project UUID"),
    "package_name": fields.String(description="Name of the created package"),
    "package_path": fields.String(description="Path of the created package"),
    "error_msg": fields.String(description="Error message")
})


def dump_swagger():
    """Dump Swagger specification in docs/rest_api.json"""
    # TODO replace this with the URL of a real tng-project service
    app.config.update(SERVER_NAME="tng-project.5gtango.eu")
    with app.app_context():
        with open(os.path.join("docs", "rest_api.json"), "w") as f:
            f.write(json.dumps(api.__schema__))


# start REST API server
def serve_forever(args, debug=True):
    """Start serving (forever) the REST API with flask"""
    # TODO replace this with WSGIServer for better performance
    log.info("Starting tng-project in service mode")
    app.cliargs = args
    app.run(host=args.service_address, port=args.service_port, debug=debug)


@api_v1.route("/pings")
class Ping(Resource):
    @api_v1.marshal_with(ping_get_model)
    def get(self):
        """Health check: Respond with current uptime"""
        uptime = None
        try:
            uptime = str(subprocess.check_output("uptime")).strip()
        except BaseException as e:
            log.warning(str(e))
        return {"alive_since": uptime}


@api_v1.route("/projects")
class Projects(Resource):
    @api_v1.marshal_with(projects_get_model)
    def get(self):
        """Get list of projects"""
        log.info("GET to /projects. Loading available projects")
        os.makedirs('projects', exist_ok=True)
        project_dirs = [name for name in os.listdir('projects') if os.path.isdir(os.path.join('projects', name))]
        return {'projects': project_dirs}

    @api_v1.expect(project_parser)
    @api_v1.marshal_with(projects_post_model)
    def post(self):
        """Create a new project and generate descriptors with the given args"""
        args = project_parser.parse_args()
        log.info("POST to /projects with args: {}".format(args))

        # transform args into array passed to the descriptorgen cli
        # create a new UUID for each project (to avoid whitespaces)
        project_uuid = str(uuid.uuid4())
        dgn_args = ['-p', os.path.join('projects', project_uuid)]

        for k, v in args.items():
            # only add --tango/--osm if value=True
            if k == 'only_tango':
                if v:
                    dgn_args.append('--tango')
            elif k == 'only_osm':
                if v:
                    dgn_args.append('--osm')
            elif k == 'image_names' or k == 'image_types':
                if v is not None:
                    dgn_args.append('--' + k)
                    # split multiple image names/types and append all of them
                    dgn_args.extend(v.split(' '))
            else:
                # convert #vnfs from int to str (CLI only accepts string)
                if k == 'vnfs':
                    v = str(v)
                # add '--' as prefix for each key to be consistent with CLI
                dgn_args.append('--' + k)
                dgn_args.append(v)
        log.debug("CLI args: {}".format(dgn_args))

        cli_args = cli.parse_args(dgn_args)
        project = cli.dispatch(cli_args)

        project_path = os.path.join('projects', project_uuid)
        project_files = [f for f in listdir(project_path) if isfile(join(project_path, f))]
        info = {'uuid': project_uuid, "error_msg": project.error_msg, "files": []}
        files = []
        for f in project_files:
            files.append('http://127.0.0.1:5098/api/v1/projects/' + project_uuid + '/' + f)

        info['files'] = files
        return info


@api_v1.route("/projects/<string:project_uuid>")
class Project(Resource):
    @api_v1.marshal_with(project_get_model)
    @api_v1.response(200, 'OK')
    @api_v1.response(404, "Project not found")
    def get(self, project_uuid):
        """Get the UUID and manifest of the specified project"""
        log.info("GET to /projects/{}".format(project_uuid))
        project_path = os.path.join('projects', project_uuid)
        if not os.path.isdir(project_path):
            log.error("No project found with name/UUID {}".format(project_uuid))
            return {'error_msg': "Project not found: {}".format(project_uuid)}, 404

        project = cli_project.load_project(project_path)
        return {"project_uuid": project_uuid, "manifest": project.project_config, "error_msg": project.error_msg}

    @api_v1.marshal_with(project_delete_model)
    @api_v1.response(200, 'OK')
    @api_v1.response(404, "Project not found")
    def delete(self, project_uuid):
        """Delete the specified project"""
        log.info("DELETE to /projects/{}".format(project_uuid))
        project_path = os.path.join('projects', project_uuid)
        if not os.path.isdir(project_path):
            log.error("No project found with name/UUID {}".format(project_uuid))
            return {'error_msg': "Project not found: {}".format(project_uuid)}, 404

        shutil.rmtree(project_path)
        return {"project_uuid": project_uuid}


@api_v1.route("/projects/<string:project_uuid>/<string:file_name>")
class ProjectSpecificFile(Resource):
    def get(self, project_uuid, file_name):
        """Get/download the specified file from the specified project"""
        log.info("GET to /projects/{}/{}".format(project_uuid, file_name))
        projects_dir = os.path.realpath('projects')
        project_path = os.path.join(projects_dir, project_uuid)
        log.debug("Project path: {}".format(project_path))
        return send_from_directory(project_path, file_name)


@api_v1.route("/projects/<string:project_uuid>/files")
class ProjectFiles(Resource):
    # get list of project files
    @api_v1.marshal_with(files_get_model)
    @api_v1.response(200, 'OK')
    @api_v1.response(404, "Project not found")
    def get(self, project_uuid):
        """Get a list of files in the specified project"""
        log.info("GET to /projects/{}/files".format(project_uuid))
        project_path = os.path.join('projects', project_uuid)
        if not os.path.isdir(project_path):
            log.error("No project found with name/UUID {}".format(project_uuid))
            return {'error_msg': "Project not found: {}".format(project_uuid)}, 404

        project = cli_project.load_project(project_path)
        return {"project_uuid": project_uuid, "files": project.project_config["files"]}

    @api_v1.expect(file_upload_parser)
    @api_v1.marshal_with(files_post_model)
    @api_v1.response(200, 'OK')
    @api_v1.response(404, "Project not found")
    def post(self, project_uuid):
        """Upload and add a file to the specified project"""
        args = file_upload_parser.parse_args()
        log.info("POST to /projects/{}/files with args: {}".format(project_uuid, args))

        # try to load the project
        project_path = os.path.join('projects', project_uuid)
        if not os.path.isdir(project_path):
            log.error("No project found with name/UUID {}".format(project_uuid))
            return {'error_msg': "Project not found: {}".format(project_uuid)}, 404
        project = cli_project.load_project(project_path)

        # check if file already exists
        file = args["file"]
        if os.path.isfile(os.path.join(project_path, file.filename)):
            log.warning("Overriding existing file {}".format(file.filename))

        # save uploaded file to project and add to project manifest
        log.debug("Adding uploaded file {} to project with UUID {}".format(file.filename, project_uuid))
        file.save(os.path.join(project_path, file.filename))
        project.add_file(os.path.join(project_path, file.filename), args["file_type"])

        return {"project_uuid": project_uuid, "filename": file.filename, "error_msg": project.error_msg}

    @api_v1.expect(filename_parser)
    @api_v1.marshal_with(files_delete_model)
    @api_v1.response(200, 'OK')
    @api_v1.response(404, "Project or file not found")
    def delete(self, project_uuid):
        """Delete the specified project"""
        args = filename_parser.parse_args()
        log.info("DELETE to /projects/{}/files with args: {}".format(project_uuid, args))

        # try to load the project
        project_path = os.path.join('projects', project_uuid)
        if not os.path.isdir(project_path):
            log.error("No project found with name/UUID {}".format(project_uuid))
            return {'error_msg': "Project not found: {}".format(project_uuid)}, 404
        project = cli_project.load_project(project_path)

        # check if file exists
        filename = args["filename"]
        if not os.path.isfile(os.path.join(project_path, filename)):
            log.error("File {} not found in project with UUID {}".format(filename, project_uuid))
            return {"project_uuid": project_uuid, "error_msg": "File {} not found in project".format(filename)}, 404

        # remove file from project manifest and delete it
        project.remove_file(os.path.join(project_path, filename))
        os.remove(os.path.join(project_path, filename))
        return {"project_uuid": project_uuid, "removed_file": filename, "error_msg": project.error_msg}


# not needed and implementation not completed; just left for possible future use
@api_v1.deprecated
@api_v1.route("/projects/<string:project_uuid>/download")
class ProjectDownload(Resource):
    """Download the specified project as zip file. Not completely implemented. Use packager instead."""
    @api_v1.response(200, 'OK')
    @api_v1.response(404, "Project not found")
    def get(self, project_uuid):
        log.info("GET to /projects/{}/download".format(project_uuid))

        # try to load the project
        project_path = os.path.join('projects', project_uuid)
        if not os.path.isdir(project_path):
            log.error("No project found with name/UUID {}".format(project_uuid))
            return {'error_msg': "Project not found: {}".format(project_uuid)}, 404
        # project = cli_project.load_project(project_path)

        # zip the project
        zip_path = os.path.join('projects', project_uuid + '.zip')
        zipped_project = zipfile.ZipFile(zip_path, 'w')
        for root, dirs, files in os.walk(project_path):
            for f in files:
                zipped_project.write(os.path.join(root, f), os.path.relpath(os.path.join(root, f), 'projects'))
        zipped_project.close()

        # TODO: return the zipped project; async?
        return "not implemented", 501


@api_v1.route("/projects/<string:project_uuid>/package")
class ProjectPackage(Resource):
    @api_v1.expect(package_parser)
    @api_v1.marshal_with(package_post_model)
    @api_v1.response(200, 'OK')
    @api_v1.response(404, "Project not found")
    @api_v1.response(503, "tng-sdk-package not installed")
    def post(self, project_uuid):
        """Package (and validate) the specified project using tng-sdk-package (if installed)"""
        args = package_parser.parse_args()
        log.info("POST to /projects/{}/package with args: {}".format(project_uuid, args))

        # try to load the project
        project_path = os.path.join('projects', project_uuid)
        if not os.path.isdir(project_path):
            log.error("No project found with name/UUID {}".format(project_uuid))
            return {'error_msg': "Project not found: {}".format(project_uuid)}, 404

        # try to import the packager if it's installed
        try:
            import tngsdk.package
        except BaseException as ex:
            log.error("Cancel packaging: tng-sdk-package not installed")
            log.debug(ex)
            return {'error_msg': "Cancel packaging: tng-sdk-package not installed"}, 503

        # call the packager
        pkg_args = [
            '--package', project_path,
            '--output', project_path,
        ]
        if args['skip_validation']:
            log.debug("Skipping validation")
            pkg_args.append('--skip-validation')
        r = tngsdk.package.run(pkg_args)
        log.debug(r)
        if r.error is not None:
            return {'project_uuid': project_uuid, 'package_name': None, 'package_path': None,
                    'error_msg': "Package error: {}".format(r.error)}
        pkg_path = r.metadata.get("_storage_location")
        pkg_name = ntpath.basename(pkg_path)
        log.debug("Package name {} and path {}".format(pkg_name, pkg_path))
        return {'project_uuid': project_uuid, 'package_name': pkg_name, 'package_path': pkg_path, 'error_msg': None}
