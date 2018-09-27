#!/usr/bin/python3

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

import sys
import os
import logging
import oyaml as yaml        # ordered yaml to avoid reordering of descriptors
import uuid
import glob
import mimetypes
import argparse
import coloredlogs
from collections import defaultdict
from tabulate import tabulate
from tngsdk.project.workspace import Workspace
from tngsdk.descriptorgen import descriptorgen
from tngsdk import rest


log = logging.getLogger(__name__)


class Project:
    CONFIG_VERSION = "4.1"

    __descriptor_name__ = 'project.yml'

    def __init__(self, workspace, prj_root, config=None, fixed_uuid=None):
        if fixed_uuid is not None:
            self.uuid = fixed_uuid
        else:
            self.uuid = str(uuid.uuid4())
        self._prj_root = prj_root
        self._workspace = workspace
        self.error_msg = None
        if config:
            self._prj_config = config
            if 'uuid' in config['package']:
                self.uuid = config['package']['uuid']
            else:
                log.warning("Couldn't retrieve the projects UUID.")
        else:
            self.load_default_config()

        # get config from workspace for URL->MIME mapping
        with open(workspace.config["projects_config"], 'r') as config_file:
            self.type_mapping = yaml.load(config_file)

    @property
    def project_root(self):
        return self._prj_root

    @property
    def nsd_root(self):
        return os.path.join(self._prj_root, 'sources', 'nsd')

    @property
    def vnfd_root(self):
        return os.path.join(self._prj_root, 'sources', 'vnf')

    @property
    def project_config(self):
        return self._prj_config

    @property
    def descriptor_extension(self):
        return self.project_config['descriptor_extension']

    def load_default_config(self):
        self._prj_config = {
            'version': self.CONFIG_VERSION,
            'package': {
                'name': '5gtango-project-sample',
                'vendor': 'eu.5gtango',
                'version': '0.1',
                'maintainer': 'Name, Company, Contact',
                'description': 'Some description about this sample',
                'uuid': self.uuid
            },
            'descriptor_extension':
                self._workspace.default_descriptor_extension,
            'files': []
        }

    # create new project (empty or with descriptors by descriptorgen)
    def create_prj(self, empty=False, dgn_args=None):
        # create project root directory (if it doesn't exist)
        log.info('Creating project at {}'.format(self._prj_root))
        if os.path.isdir(self._prj_root):
            print("Unable to create project at '{}'. Directory already exists."
                  .format(self._prj_root), file=sys.stderr)
            exit(1)
        os.makedirs(self._prj_root, exist_ok=False)

        # create subdirs, sample descriptors, and project.yml
        if empty:
            log.debug('Creating empty project (no folders or sample files)')
        else:
            self._gen_descriptors(dgn_args)
        self._write_prj_yml()

    # generate descriptors using the descriptorgen module and specified args
    def _gen_descriptors(self, dgn_args):
        dgn_args.out_path = self._prj_root
        log.info("Generating descriptors")
        log.debug("Descriptor generation args: {}".format(dgn_args))
        descriptorgen.generate(dgn_args)

        # add generated files to project manifest
        log.debug("Adding generated descriptors to project manifest")
        self.add_file(os.path.join(self._prj_root, "*"))

    # writes project descriptor to file (project.yml)
    def _write_prj_yml(self):
        prj_path = os.path.join(self._prj_root, Project.__descriptor_name__)
        with open(prj_path, 'w') as prj_file:
            prj_file.write(yaml.dump(self._prj_config,
                                     default_flow_style=False))

    # resolves wildcards by calling add/remove_file for each file
    def resolve_wildcards(self, path, add=False, remove=False):
        for f in glob.glob(path):
            if add:
                self.add_file(f)
            if remove:
                self.remove_file(f)

    # detects and returns MIME type of specified file
    def mime_type(self, file):
        name, extension = os.path.splitext(file)

        # check yml files to detect and classify 5GTANGO descriptors
        if extension == ".yml" or extension == ".yaml":
            with open(file, 'r') as yml_file:
                yml_file = yaml.load(yml_file)
                if 'descriptor_schema' in yml_file:
                    type = self.type_mapping[yml_file['descriptor_schema']]
                # try to detect OSM descriptors based on field names
                elif 'constituent-vnfd' in yml_file and 'vld' in yml_file:
                    type = 'application/vnd.etsi.osm.nsd'
                elif 'vnfd-catalog' in yml_file:
                    type = 'application/vnd.etsi.osm.vnfd'
                else:
                    log.warning('Could not detect MIME type of {}. '
                                'Using text/yaml'.format(file))
                    type = 'text/yaml'

        # for non-yml files determine the type using mimetypes
        else:
            (type, encoding) = mimetypes.guess_type(file, strict=False)
            # add more types from a config with mimetypes.read_mime_types(file)

        log.debug('Detected MIME type: {}'.format(type))
        return type

    # adds a file to the project: detects type and adds to project.yml
    def add_file(self, file_path, type=None):
        # resolve wildcards
        if '*' in file_path:
            log.debug('Attempting to resolve wildcard in {}'.format(file_path))
            self.resolve_wildcards(file_path, add=True)
            return

        # try to detect the MIME type if none is given
        if type is None:
            type = self.mime_type(file_path)
        if type is None:
            log.warning('Could not detect MIME type of {}. Using "application/octet-stream".'.format(file_path))
            self.error_msg = 'Could not detect MIME type of {}. Using "application/octet-stream".'.format(file_path)
            type = "application/octet-stream"       # default MIME type

        # set tags accordingly
        tags = []
        if '5gtango' in type:
            tags = ['eu.5gtango']
        elif 'osm' in type:
            tags = ['etsi.osm']

        # calculate relative file path to project root
        abs_file_path = os.path.abspath(file_path)
        abs_prj_root = os.path.abspath(self._prj_root)
        rel_file_path = os.path.relpath(abs_file_path, abs_prj_root)
        # fix windows paths by replacing \ with /
        if os.name == 'nt':
            rel_file_path = rel_file_path.replace('\\', '/')
            log.debug('Adjusted Windows path in project.yml: {}'.format(rel_file_path))

        # add to project.yml
        file = {'path': rel_file_path, 'type': type, 'tags': tags}
        if file in self._prj_config['files']:
            log.warning('{} is already in project.yml.'.format(file_path))
        else:
            self._prj_config['files'].append(file)
            self._write_prj_yml()
            log.info('Added {} to project.yml'.format(file_path))

    # removes a file from the project
    def remove_file(self, file_path):
        # resolve wildcards
        if '*' in file_path:
            log.debug('Attempting to resolve wildcard in {}'.format(file_path))
            self.resolve_wildcards(file_path, remove=True)
            return

        # calculate relative file path to project root (similar to add_file)
        abs_file_path = os.path.abspath(file_path)
        abs_prj_root = os.path.abspath(self._prj_root)
        rel_file_path = os.path.relpath(abs_file_path, abs_prj_root)
        # adjust to windows paths by replacing \ with /
        if os.name == 'nt':
            rel_file_path = rel_file_path.replace('\\', '/')
            log.debug('Adjusted relative Windows path to match project.yml: {}'.format(rel_file_path))

        for f in self._prj_config['files']:
            if f['path'] == rel_file_path:
                self._prj_config['files'].remove(f)
                self._write_prj_yml()
                log.info('Removed {} from project.yml'.format(file_path))
                return
        log.warning('{} is not in project.yml'.format(file_path))

    # prints project info/status
    def status(self):
        # print general info
        print('Project: {}'.format(self._prj_config['package']['name']))
        print('Vendor: {}'.format(self._prj_config['package']['vendor']))
        print('Version: {}'.format(self._prj_config['package']['version']))
        if 'uuid' in self._prj_config['package']:
            print('UUID: {}'.format(self._prj_config['package']['uuid']))
        else:
            print('UUID: None')
        print(self._prj_config['package']['description'])

        if 'files' not in self._prj_config:
            log.warning('Old SONATA project: project.yml does not have a files section!'
                        'To translate an old SONATA project to a new 5GTANGO project, use --translate')
            return

        # collect and print info about involved MIME types (type + quanity)
        types = defaultdict(int)
        for f in self._prj_config['files']:
            types[f['type']] += 1
        print(tabulate(types.items(), ['MIME type', 'Quantity'], 'grid'))

    # translate old SONATA VNFD or NSD to new 5GTANGO format (descriptor_version --> descriptor_schema)
    def translate_descriptor(self, descriptor_file, vnfd):
        log.info('Translating descriptor {}'.format(descriptor_file))
        with open(descriptor_file, 'r') as f:
            descriptor = yaml.load(f)

        descriptor.pop('descriptor_version')
        if vnfd:
            schema = self.type_mapping['application/vnd.5gtango.vnfd']
        else:
            schema = self.type_mapping['application/vnd.5gtango.nsd']
        descriptor['descriptor_schema'] = schema

        with open(descriptor_file, 'w') as f:
            f.write(yaml.dump(descriptor, default_flow_style=False))

    # translate old SONATA project to new 5GTANGO project (in place)
    def translate(self):
        log.debug('Attempting to translate old SONATA project to new 5GTANGO '
                  'project (in place): {}'.format(self._prj_root))

        # update/set version number to current version
        log.debug('Updating version number to {}'.format(self.CONFIG_VERSION))
        self._prj_config['version'] = self.CONFIG_VERSION

        # update descriptors: replace "schema_version" with "descriptor_schema" based on nsd/vnf folder
        log.debug('Updating old SONATA descriptors to new 5GTANGO descriptors')
        vnfd_path = os.path.join(self._prj_root, 'sources', 'vnf', '**', '*.yml')
        for vnfd in glob.glob(vnfd_path, recursive=True):
            if os.path.isfile(vnfd):
                self.translate_descriptor(vnfd, vnfd=True)
        nsd_path = os.path.join(self._prj_root, 'sources', 'nsd', '**', '*.yml')
        for nsd in glob.glob(nsd_path, recursive=True):
            if os.path.isfile(nsd):
                self.translate_descriptor(nsd, vnfd=False)

        # create files section and add files
        log.debug('Creating "files" section and adding all files in {}'.format(self._prj_root))
        self._prj_config['files'] = []
        for f in glob.glob(os.path.join(self._prj_root, 'sources', '**'), recursive=True):
            if os.path.isfile(f):
                self.add_file(f)

        self._write_prj_yml()
        log.info('Successfully translated {} to 5GTANGO project.'.format(self._prj_root))

    # return a list of relative file paths to all NSDs (default: Tango NSDs)
    def get_nsds(self, type='application/vnd.5gtango.nsd'):
        return self.get_file_paths(type)

    # return a list of relative file paths to all VNFDs (default: Tango VNFDs)
    def get_vnfds(self, type='application/vnd.5gtango.vnfd'):
        return self.get_file_paths(type)

    # return a list of relative (to proj root) file paths to files of the specified type
    def get_file_paths(self, type):
        return [f['path'] for f in self._prj_config['files'] if f['type'] == type]

    @staticmethod
    def __is_valid__(project):
        """Checks if a given project is valid"""
        if type(project) is not Project:
            return False

        if not os.path.isfile(os.path.join(
                project.project_root,
                Project.__descriptor_name__)):
            return False

        return True

    # loads a project using its project manifest (project.yml)
    @staticmethod
    def load_project(prj_root, workspace=None, translate=False):
        # load default workspace if none specified
        if workspace is None:
            workspace = Workspace.load_workspace(Workspace.DEFAULT_WORKSPACE_DIR)

        # check if project manifest exists
        prj_filename = os.path.join(prj_root, Project.__descriptor_name__)
        if not os.path.isdir(prj_root) or not os.path.isfile(prj_filename):
            log.error("Unable to load project manifest '{}'".format(prj_filename))
            return None

        # load project manifest
        log.info("Loading project '{}'".format(prj_filename))
        with open(prj_filename, 'r') as prj_file:
            try:
                prj_config = yaml.load(prj_file)
            except yaml.YAMLError as exc:
                log.error("Error parsing descriptor file: {0}".format(exc))
                return
            if not prj_config:
                log.error("Couldn't read descriptor file: '{0}'".format(prj_file))
                return

        # create a new project object with the same manifest
        if prj_config['version'] == Project.CONFIG_VERSION:
            return Project(workspace, prj_root, config=prj_config)

        # deal with different versions
        if prj_config['version'] < Project.CONFIG_VERSION and not translate:
            log.warning("Project version {} is outdated. To translate to new 5GTANGO project version use --translate"
                      .format(prj_config['version']))
        if prj_config['version'] > Project.CONFIG_VERSION:
            log.warning("Project version {} is ahead of the current version {}."
                      .format(prj_config['version'], Project.CONFIG_VERSION))

        return Project(workspace, prj_root, config=prj_config)


def parse_args_project(input_args=None):
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description="5GTANGO SDK project")
    # project CLI
    parser.add_argument("-p", "--project",
                        help="create a new project at the specified location",
                        required=False,
                        default='new-project')

    parser.add_argument("-w", "--workspace",
                        help="location of existing (or new) workspace. "
                        "If not specified will assume '{}'"
                        .format(Workspace.DEFAULT_WORKSPACE_DIR),
                        required=False)

    parser.add_argument("--empty",
                        help="create an empty project (without sample files)",
                        required=False,
                        action="store_true")

    parser.add_argument("-v", "--debug",
                        help="increases logging level to debug",
                        required=False,
                        action="store_true")

    parser.add_argument("--add",
                        help="Add file to project",
                        required=False,
                        default=None)

    parser.add_argument("-t", "--type",
                        help="MIME type of added file (only with --add)",
                        required=False,
                        default=None)

    parser.add_argument("--remove",
                        help="Remove file from project",
                        required=False,
                        default=None)

    parser.add_argument("--status",
                        help="Show project file paths",
                        required=False,
                        action="store_true")

    parser.add_argument("--translate",
                        help="Translate old SONATA project to new 5GTANGO project",
                        required=False,
                        action="store_true")

    # service management
    parser.add_argument("-s", "--service",
                        help="Run tng-project in service mode with REST API.",
                        required=False,
                        default=False,
                        dest="service",
                        action="store_true")

    parser.add_argument("--dump-swagger",
                        help="Dump Swagger JSON of REST API and exit",
                        required=False,
                        default=False,
                        dest="dump_swagger",
                        action="store_true")

    parser.add_argument("--address",
                        help="Listen address of REST API when in service mode.",
                        required=False,
                        default="localhost",
                        dest="service_address")

    parser.add_argument("--port",
                        help="TCP port of REST API when in service mode.",
                        required=False,
                        default=5098,
                        dest="service_port")

    if input_args is None:
        input_args = sys.argv[1:]
    return parser.parse_known_args(input_args)


# create and return project
def create_project(args=None, extra_args=None, fixed_uuid=None):
    if args is None:
        args, extra_args = parse_args_project()

    if args.debug:
        coloredlogs.install(level='DEBUG')
    else:
        coloredlogs.install(level='INFO')

    # pass extra_args arguments to descriptorgen (to check if descriptorgen knows them)
    dgn_args = None
    if extra_args is not None:
        log.debug("Passing these parameters to descriptorgen: {}".format(extra_args))
        dgn_args = descriptorgen.parse_args(extra_args)

    # dump Swagger REST API specification
    if args.dump_swagger:
        rest.dump_swagger()
        log.info("Dumped Swagger API spec to docs/rest_api.json")
        exit(0)

    # start service with REST API (instead of using CLI)
    if args.service:
        rest.serve_forever(args)
        exit(0)

    # use specified workspace or default
    if args.workspace:
        ws_root = os.path.expanduser(args.workspace)
    else:
        ws_root = Workspace.DEFAULT_WORKSPACE_DIR

    ws = Workspace.load_workspace(ws_root)
    if not ws:
        print("Could not find a 5GTANGO workspace at the specified location",
              file=sys.stderr)
        exit(1)

    prj_root = os.path.expanduser(args.project)

    if args.add:
        # load project and add file to project.yml
        log.debug("Attempting to add file {}".format(args.add))
        proj = Project.load_project(prj_root, ws)
        proj.add_file(args.add, type=args.type)

    elif args.remove:
        # load project and remove file from project.yml
        log.debug("Attempting to remove file {}".format(args.remove))
        proj = Project.load_project(prj_root, ws)
        proj.remove_file(args.remove)

    elif args.status:
        # load project and show status
        log.debug("Attempting to show project status")
        proj = Project.load_project(prj_root, ws)
        proj.status()

    elif args.translate:
        proj = Project.load_project(prj_root, ws, translate=True)
        proj.translate()

    else:
        # create project
        log.debug("Attempting to create a new project")
        proj = Project(ws, prj_root, fixed_uuid=fixed_uuid)
        proj.create_prj(args.empty, dgn_args)
        log.debug("Project created.")

    return proj


if __name__ == '__main__':
    project = create_project()
