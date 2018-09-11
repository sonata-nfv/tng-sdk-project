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
import tngsdk.project.workspace as workspace
import tngsdk.project.project as cli


class TestProjectCLI:
    # create and return a temporary workspace 'test-ws'
    @pytest.fixture(scope='module')
    def workspace(self):
        # start clean without workspace
        if os.path.isdir('test-ws'):
            shutil.rmtree('test-ws')

        args = workspace.parse_args_workspace([
            '-w', 'test-ws',
            '--debug'
        ])
        workspace.init_workspace(args)
        assert os.path.isdir('test-ws')
        yield 'test-ws'
        shutil.rmtree('test-ws')

    # create and return a new temporary project 'test-project'
    @pytest.fixture(scope='module')
    def project(self, workspace):
        args, extra_ars = cli.parse_args_project([
            '-p', 'test-project',
            '-w', workspace,
            '--debug'
        ])
        project = cli.create_project(args, extra_ars)
        assert os.path.isdir('test-project')
        assert os.path.isfile(os.path.join('test-project', 'project.yml'))
        yield project
        shutil.rmtree('test-project')

    # TODO: add tests using descriptorgen

    # add a file to the test project
    def test_add_remove_file(self, workspace, project):
        project_path = project.project_root

        # create new text file inside the project
        file_path = os.path.join(project_path, 'sample.txt')
        with open(file_path, 'w') as open_file:
            open_file.write('sample text')
        assert os.path.isfile(file_path)

        # add to project.yml
        args, extra_args = cli.parse_args_project([
            '-w', workspace,
            '-p', str(project_path),
            '--add', str(file_path),
            '--debug'
        ])
        cli.create_project(args, extra_args)
        project_yml_path = os.path.join(project_path, 'project.yml')
        with open(project_yml_path) as open_file:
            project_yml = yaml.load(open_file)
            project_files = [f['path'] for f in project_yml['files']]
            assert 'sample.txt' in project_files

        # remove sample.txt
        args, extra_args = cli.parse_args_project([
            '-w', workspace,
            '-p', str(project.project_root),
            '--remove', os.path.join(project.project_root, 'sample.txt'),
            '--debug'
        ])
        project = cli.create_project(args, extra_args)

        # check if NSD was removed
        with open(project_yml_path) as open_file:
            project_yml = yaml.load(open_file)
            project_files = [f['path'] for f in project_yml['files']]
            assert not 'sample.txt' in project_files
