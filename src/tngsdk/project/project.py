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


log = logging.getLogger(__name__)


class Project:

    BACK_CONFIG_VERSION = "0.4"
    CONFIG_VERSION = "0.5"

    __descriptor_name__ = 'project.yml'

    def __init__(self, workspace, prj_root, config=None):
        coloredlogs.install(level=workspace.log_level)
        self._prj_root = prj_root
        self._workspace = workspace
        if config:
            self._prj_config = config
        else:
            self.load_default_config()

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
                'name': 'sonata-project-sample',
                'vendor': 'eu.sonata-nfv.package',
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
        src_subdirs = {'ssm', 'pattern', 'vnf', 'nsd'}

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
        for d in src_subdirs:
            if d == 'nsd':
                path = os.path.join(src_path, d)
            else:
                path = os.path.join(src_path, d, 'sample')
            os.makedirs(path, exist_ok=True)
            self._create_sample(d, path)

        self._create_vnf_dir()
        self._create_nsd_dir()

    def _create_vnf_dir(self, name='sample'):
        """
        Function to create a new VNF inside project source.
        :param name:The VNF name
        """
        vnf_subdirs = {'fsm'}
        vnf_path = os.path.join(self.vnfd_root, name)
        self._create_sample('vnf', vnf_path)
        for d in vnf_subdirs:
            path = os.path.join(vnf_path, d)
            os.makedirs(path, exist_ok=False)

    def _create_nsd_dir(self):
        """
        Function to create a new NSD inside project source.
        """
        self._create_sample('nsd', self.nsd_root)

    # writes project descriptor to file (project.yml)
    def _write_prj_yml(self):
        prj_path = os.path.join(self._prj_root, Project.__descriptor_name__)
        with open(prj_path, 'w') as prj_file:
            prj_file.write(yaml.dump(self._prj_config,
                                     default_flow_style=False))

    def get_ns_descriptor(self):
        """
        Obtain the file list of NS descriptors
        :return:
        """
        nsd_list = [os.path.join(self.nsd_root, file)
                    for file in os.listdir(self.nsd_root)
                    if os.path.isfile(os.path.join(self.nsd_root, file)) and
                    file.endswith(self.descriptor_extension)]

        if len(nsd_list) == 0:
            log.error("Project does not contain a NS Descriptor")
            return

        if len(nsd_list) != 1:
            log.warning("Project contains more than one NS Descriptor")

        return nsd_list

    def get_vnf_descriptors(self):
        """
        Obtain the file list of VNF descriptors
        :return:
        """
        vnfd_list = []
        for root, dirs, files in os.walk(self.vnfd_root):
            for file in files:
                if file.endswith(self.descriptor_extension):
                    vnfd_list.append(os.path.join(root, file))
        return vnfd_list

    def _create_sample(self, prj_type, path):
        switcher = {
            # 'fsm': self._create_sample_fsm,
            'ssm': self._create_sample_ssm,
            'pattern': self._create_sample_pattern,
            'vnf': self._create_sample_vnf,
            'nsd': self._create_sample_nsd
        }
        func = switcher.get(prj_type)
        if func is None:
            log.error("Could not create sample for "
                      "" + prj_type + ", unknown project type")
            return

        func(path)

    # TODO: add created sample files to project.yml
    def _create_sample_fsm(self, path):
        d = {
            'name': 'sample fsm',
            'id': 'com.sonata.fsm.sample',
            'version': '0.1'
        }
        prj_path = os.path.join(path, 'fsm.yml')
        with open(prj_path, 'w') as prj_file:
            prj_file.write(yaml.dump(d))

        # add to project.yml
        file = {'path': prj_path, 'type': 'application/vnd.5gtango.fsm',
                'tags': ['eu.5gtango', 'eu.sonata']}
        self._prj_config['files'].append(file)

    def _create_sample_ssm(self, path):
        d = {
            'name': 'sample ssm',
            'id': 'com.sonata.ssm.sample',
            'version': '0.1'
        }
        prj_path = os.path.join(path, 'ssm.yml')
        with open(prj_path, 'w') as prj_file:
            prj_file.write(yaml.dump(d))

        # add to project.yml
        file = {'path': prj_path, 'type': 'application/vnd.5gtango.ssm',
                'tags': ['eu.5gtango', 'eu.sonata']}
        self._prj_config['files'].append(file)

    # TODO: what is this? do we need it in tango? what's the MIME type?
    def _create_sample_pattern(self, path):
        d = {
            'name': 'sample pattern',
            'id': 'com.sonata.pattern.sample',
            'version': '0.1'
        }
        prj_path = os.path.join(path, 'patterm.yml')
        with open(prj_path, 'w') as prj_file:
            prj_file.write(yaml.dump(d))

        # add to project.yml
        file = {'path': prj_path, 'type': 'application/vnd.5gtango.pattern',
                'tags': ['eu.5gtango', 'eu.sonata']}
        self._prj_config['files'].append(file)

    def _create_sample_vnf(self, path):
        """
        Create a sample VNF descriptor
        (to be evoked upon project creation)

        :param path: The VNF sample directory
        """
        sample_vnfd = 'vnfd-sample.yml'
        sample_image = 'sample_docker'
        rp = __name__

        # Copy sample VNF descriptor
        src_path = os.path.join('samples', sample_vnfd)
        srcfile = pkg_resources.resource_filename(rp, src_path)
        shutil.copyfile(srcfile, os.path.join(path, sample_vnfd))

        # add to project.yml
        file = {'path': src_path, 'type': 'application/vnd.5gtango.vnfd',
                'tags': ['eu.5gtango']}
        self._prj_config['files'].append(file)

        # Copy associated sample VM image
        src_path = os.path.join('samples', sample_image)
        srcfile = pkg_resources.resource_filename(rp, src_path)
        shutil.copyfile(srcfile, os.path.join(path, sample_image))

        # FIXME: what's the MIME tpye?
        # add to project.yml
        file = {'path': src_path, 'type': 'application/vnd.5gtango.fsm',
                'tags': ['eu.5gtango']}
        self._prj_config['files'].append(file)

    def _create_sample_nsd(self, path):
        """
        Create a sample NS descriptor
        (to be evoked upon project creation)

        :param path: The NSD sample directory
        """
        sample_nsd = 'nsd-sample.yml'
        rp = __name__

        # Copy sample NS descriptor
        src_path = os.path.join('samples', sample_nsd)
        srcfile = pkg_resources.resource_filename(rp, src_path)
        shutil.copyfile(srcfile, os.path.join(path, sample_nsd))

        # add to project.yml
        file = {'path': src_path, 'type': 'application/vnd.5gtango.nsd',
                'tags': ['eu.5gtango']}
        self._prj_config['files'].append(file)

    # adds a file to the project: detects type and adds to project.yml
    def add_file(self, file):
        name, extension = os.path.splitext(file)

        # check yml files to detect and classify 5GTANGO descriptors
        if extension == ".yml" or extension == ".yaml":
            yml_file = yaml.load(file)
            schema_url = yml_file["descriptor_schema"]
            if schema_url:
                schema = schema_url.split("/")[-1]
                # TODO: maybe easier to simply include MIME type in schema and retrieve it from there instead of somehow reconstructing it from the url? but requires internet conn...

            else:
                pass        # TODO: use plain text

        else:
            pass    # TODO: try to use python-magic or ask user

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
