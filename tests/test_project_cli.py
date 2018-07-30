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

import pytest
import os
import shutil
import yaml
from tngsdk.project.project import Project
import tngsdk.project.project as cli


class TestProjectCLI:
    # create and return a new temporary project 'test-project'
    @pytest.fixture(scope='module')
    def project(self, tmpdir_factory):
        tmpdir_factory.mktemp('test-dir')
        args = cli.parse_args_project(['-p', 'test-dir/test-project'])
        project = cli.create_project(args)
        assert os.path.isdir('test-dir/test-project')
        assert os.path.isfile(os.path.join('test-dir', 'test-project', 'project.yml'))
        yield project
        shutil.rmtree('test-dir')

    # add a file to the test project
    def test_add_file(self, project):
        project_path = project.project_root

        # create new text file inside the project
        file_path = os.path.join(project_path, 'sample.txt')
        with open(file_path, 'w') as open_file:
            open_file.write('sample text')
        assert os.path.isfile(file_path)

        # add to project.yml
        args = cli.parse_args_project([
            '-p', str(project_path),
            '--add', str(file_path),
            '--debug'
        ])
        cli.create_project(args)
        project_yml_path = os.path.join(project_path, 'project.yml')
        with open(project_yml_path) as open_file:
            project_yml = yaml.load(open_file)
            project_files = [f['path'] for f in project_yml['files']]
            assert 'sample.txt' in project_files

    # remove a file from the test project
    def test_remove_file(self, project):
        # check if sample NSD exists
        project_files = [f['path'] for f in project.project_config['files']]
        assert any('nsd-sample.yml' in path for path in project_files)

        # remove sample NSD
        args = cli.parse_args_project([
            '-p', str(project.project_root),
            '--remove', os.path.join(project.project_root, 'sources', 'nsd', 'nsd-sample.yml'),
            '--debug'
        ])
        project = cli.create_project(args)

        # check if NSD was removed
        project_files = [f['path'] for f in project.project_config['files']]
        assert not any('nsd-sample.yml' in path for path in project_files)
