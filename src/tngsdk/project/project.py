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
import coloredlogs
import yaml
import shutil
import pkg_resources
import magic


log = logging.getLogger(__name__)


class Project:

    BACK_CONFIG_VERSION = "0.4"
    CONFIG_VERSION = "0.5"

    __descriptor_name__ = 'project.yml'

    def __init__(self, workspace, prj_root, config=None):
        self._prj_root = prj_root
        self._workspace = workspace
        if config:
            self._prj_config = config
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
                'description': 'Some description about this sample'
            },
            'descriptor_extension':
                self._workspace.default_descriptor_extension,
            'files': []
        }

    def create_prj(self):
        log.info('Creating project at {}'.format(self._prj_root))

        self._create_dirs()
        self._write_prj_yml()

    def _create_dirs(self):
        """
        Creates the directory tree of the project
        :return:
        """
        directories = {'sources', 'dependencies', 'deployment'}
        src_subdirs = {'vnfd', 'nsd'}

        # Check if dir exists
        if os.path.isdir(self._prj_root):
            print("Unable to create project at '{}'. "
                  "Directory already exists."
                  .format(self._prj_root), file=sys.stderr)
            exit(1)

        os.makedirs(self._prj_root, exist_ok=False)
        for d in directories:
            path = os.path.join(self._prj_root, d)
            os.makedirs(path, exist_ok=True)

        src_path = os.path.join(self._prj_root, 'sources')
        vnfd_path = os.path.join(src_path, 'vnfd')
        nsd_path = os.path.join(src_path, 'nsd')
        os.makedirs(vnfd_path, exist_ok=True)
        os.makedirs(nsd_path, exist_ok=True)
        self._create_vnfd(vnfd_path)
        self._create_nsd(nsd_path)

    # create directory and sample VNFD
    def _create_vnfd(self, path):
        sample_vnfd = 'vnfd-sample.yml'
        vnfd_path = os.path.join(path, sample_vnfd)
        sample_image = 'sample_docker'
        image_path = os.path.join(path, sample_image)
        rp = __name__

        # Copy sample VNF descriptor
        src_path = os.path.join('samples', sample_vnfd)
        srcfile = pkg_resources.resource_filename(rp, src_path)
        shutil.copyfile(srcfile, vnfd_path)
        self.add_file(vnfd_path)

        # Copy associated sample VM image
        src_path = os.path.join('samples', sample_image)
        srcfile = pkg_resources.resource_filename(rp, src_path)
        shutil.copyfile(srcfile, image_path)
        self.add_file(image_path)

    # create NSD
    def _create_nsd(self, path):
        sample_nsd = 'nsd-sample.yml'
        nsd_path = os.path.join(path, sample_nsd)
        rp = __name__

        # Copy sample NS descriptor
        src_path = os.path.join('samples', sample_nsd)
        srcfile = pkg_resources.resource_filename(rp, src_path)
        shutil.copyfile(srcfile, nsd_path)
        self.add_file(nsd_path)

    # writes project descriptor to file (project.yml)
    def _write_prj_yml(self):
        prj_path = os.path.join(self._prj_root, Project.__descriptor_name__)
        with open(prj_path, 'w') as prj_file:
            prj_file.write(yaml.dump(self._prj_config,
                                     default_flow_style=False))

    # detects and returns MIME type of specified file
    def mime_type(self, file):
        name, extension = os.path.splitext(file)

        # check yml files to detect and classify 5GTANGO descriptors
        if extension == ".yml" or extension == ".yaml":
            with open(file, 'r') as yml_file:
                yml_file = yaml.load(yml_file)
                schema_url = yml_file["descriptor_schema"]
                if schema_url:
                    type = self.type_mapping[schema_url]
                else:
                    log.warning('Could not detect MIME type of {}. '
                                'Using text/yaml'.format(file))
                    type = 'text/yaml'

        # for non-yml files determine the type using python-magic
        else:
            type = magic.from_file(file, mime=True)
            # TODO: ask user if unsure

        log.debug('Detected MIME type: {}'.format(type))
        return type

    # adds a file to the project: detects type and adds to project.yml
    def add_file(self, file_path):
        type = self.mime_type(file_path)

        # add to project.yml
        file = {'path': file_path, 'type': type, 'tags': ['eu.5gtango']}
        if file in self._prj_config['files']:
            log.warning('{} is already in project.yml.'.format(file_path))
        else:
            self._prj_config['files'].append(file)
            self._write_prj_yml()
            log.info('Added {} to project.yml'.format(file_path))

    # removes a file from the project
    def remove_file(self, file_path):
        for f in self._prj_config['files']:
            if f['path'] == file_path:
                self._prj_config['files'].remove(f)
                self._write_prj_yml()
                log.info('Removed {} from project.yml'.format(file_path))
                return
        log.warning('{} is not in project.yml'.format(file_path))

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

    @staticmethod
    def __create_from_descriptor__(workspace, prj_root):
        """
        Creates a Project object based on a configuration descriptor
        :param prj_root: base path of the project
        :return: Project object
        """
        prj_filename = os.path.join(prj_root, Project.__descriptor_name__)
        if not os.path.isdir(prj_root) or not os.path.isfile(prj_filename):
            log.error("Unable to load project descriptor '{}'"
                      .format(prj_filename))

            return None

        log.info("Loading Project configuration '{}'"
                 .format(prj_filename))

        with open(prj_filename, 'r') as prj_file:
            try:
                prj_config = yaml.load(prj_file)

            except yaml.YAMLError as exc:
                log.error("Error parsing descriptor file: {0}".format(exc))
                return

            if not prj_config:
                log.error("Couldn't read descriptor file: '{0}'"
                          .format(prj_file))
                return

        if prj_config['version'] == Project.CONFIG_VERSION:
            return Project(workspace, prj_root, config=prj_config)

        # Protect against invalid versions
        if prj_config['version'] < Project.BACK_CONFIG_VERSION:
            log.error("Project configuration version '{0}' is no longer "
                      "supported (<{1})".format(prj_config['version'],
                                                Project.CONFIG_VERSION))
            return
        if prj_config['version'] > Project.CONFIG_VERSION:
            log.error("Project configuration version '{0}' is ahead of the "
                      "current supported version (={1})"
                      .format(prj_config['version'], Project.CONFIG_VERSION))
            return

        # Make adjustments to support backwards compatibility
        # 0.4
        if prj_config['version'] == "0.4":

            prj_config['package'] = {'name': prj_config['name'],
                                     'vendor': prj_config['vendor'],
                                     'version': '0.1',
                                     'maintainer': prj_config['maintainer'],
                                     'description': prj_config['description']
                                     }
            prj_config.pop('name')
            prj_config.pop('vendor')
            prj_config.pop('maintainer')
            prj_config.pop('description')
            log.warning("Loading project with an old configuration "
                        "version ({0}). Modified project configuration: {1}"
                        .format(prj_config['version'], prj_config))

        return Project(workspace, prj_root, config=prj_config)
