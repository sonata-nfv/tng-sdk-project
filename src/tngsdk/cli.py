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

import logging
import argparse
import sys
import os
from tngsdk.project.workspace import Workspace
from tngsdk.project.project import Project

log = logging.getLogger(__name__)


def parse_args(input_args=None):
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description="5GTANGO SDK project")

    parser.add_argument("-v", "--debug",
                        help="increases logging level to debug",
                        required=False,
                        action="store_true")

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

    # descriptorgen CLI
    parser.add_argument('-o', help='set relative output path',
                        required=False, default='.', dest='out_path')
    parser.add_argument('--tango', help='only generate 5GTANGO descriptors',
                        required=False, action='store_true')
    parser.add_argument('--osm', help='only generate OSM descriptors',
                        required=False, action='store_true')
    parser.add_argument('--author', help='set a specific NSD and VNFD author',
                        required=False, default='5GTANGO Developer', dest='author')
    parser.add_argument('--vendor', help='set a specific NSD and VNFD vendor',
                        required=False, default='eu.5gtango', dest='vendor')
    parser.add_argument('--name', help='set a specific NSD name',
                        required=False, default='tango-nsd', dest='name')
    parser.add_argument('--description', help='set a specific NSD description',
                        required=False, default='Default description',
                        dest='description')
    parser.add_argument('--vnfs', help='set a specific number of VNFs',
                        type=int, required=False, default=1, dest='vnfs')
    parser.add_argument('--image_names',
                        help='list of VNF image names (default: ubuntu)',
                        nargs='*', required=False, default='')
    parser.add_argument('--image_types',
                        help='list of VNF image types (default: docker)',
                        nargs='*', required=False, default='')

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
                        default="0.0.0.0",
                        dest="service_address")

    parser.add_argument("--port",
                        help="TCP port of REST API when in service mode.",
                        required=False,
                        default=5098,
                        dest="service_port")

    if input_args is None:
        input_args = sys.argv[1:]
    return parser.parse_args(input_args)


# handle cli input to create/modify project
def dispatch(args):
    if args is None:
        args = parse_args()

    # use specified workspace or default
    if args.workspace:
        ws_root = os.path.expanduser(args.workspace)
    else:
        ws_root = Workspace.DEFAULT_WORKSPACE_DIR

    ws = Workspace.load_workspace(ws_root)
    if not ws:
        log.error("Could not find a 5GTANGO workspace at the specified location")
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

        if args.vnfs != len(args.image_names):
            log.info("Number of VNFs and VNF image names don't match."
                     " Using default image names if necessary.")
        if args.vnfs != len(args.image_types):
            log.info("Number of VNFs and VNF image types don't match."
                     " Using default image types if necessary.")

        proj = Project(ws, prj_root)
        proj.create_prj(args)
        log.debug("Project created.")

    return proj
