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
from tngsdk.project.workspace import Workspace
import tngsdk.cli as cli
from tngsdk.project.project import Project


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
        args = cli.parse_args([
            '-p', 'test-project',
            '-w', workspace,
            '--debug',
            '--author', 'test.author',
            '--vendor', 'test.vendor',
            '--vnfs', '2'
        ])
        project = cli.dispatch(args)
        assert os.path.isdir('test-project')
        assert os.path.isfile(os.path.join('test-project', 'project.yml'))
        yield project
        shutil.rmtree('test-project')

    # load example-project: ensure loading works and example is up-to-date
    def test_load_example_project(self, capsys, workspace):
        ws = Workspace.load_workspace(workspace)
        project = Project.load_project('example-project', workspace=ws)
        project.status()

        # assert that the status is printed correctly
        stdout = capsys.readouterr().out
        assert all(x in stdout for x in ['Project:', 'Vendor:', 'Version:'])
        assert all(x in stdout for x in ['MIME type', 'Quantity'])

    # check generated descriptors (integration with descriptorgen)
    def test_generated_descriptors(self, project):
        # test if all descriptors exist
        assert os.path.isfile(os.path.join(project.project_root, 'tango_nsd.yml'))
        assert os.path.isfile(os.path.join(project.project_root, 'tango_vnfd0.yml'))
        assert os.path.isfile(os.path.join(project.project_root, 'tango_vnfd1.yml'))
        assert os.path.isfile(os.path.join(project.project_root, 'osm_nsd.yml'))
        assert os.path.isfile(os.path.join(project.project_root, 'osm_vnfd0.yml'))
        assert os.path.isfile(os.path.join(project.project_root, 'osm_vnfd1.yml'))

        # test if fields are set correctly
        with open(os.path.join(project.project_root, 'tango_nsd.yml'), 'r') as f:
            tango_nsd = yaml.load(f)
            assert tango_nsd['author'] == 'test.author'
            assert tango_nsd['vendor'] == 'test.vendor'
            assert len(tango_nsd['network_functions']) == 2
        with open(os.path.join(project.project_root, 'osm_nsd.yml'), 'r') as f:
            osm_nsd = yaml.load(f)
            assert osm_nsd['vendor'] == 'test.vendor'
            assert len(osm_nsd['constituent-vnfd']) == 2

    # add a file to the test project
    def test_add_remove_file(self, workspace, project):
        project_path = project.project_root

        # create new text file inside the project
        file_path = os.path.join(project_path, 'sample.txt')
        with open(file_path, 'w') as open_file:
            open_file.write('sample text')
        assert os.path.isfile(file_path)

        # add to project.yml
        args = cli.parse_args([
            '-w', workspace,
            '-p', str(project_path),
            '--add', str(file_path),
            '--debug'
        ])
        cli.dispatch(args)
        project_yml_path = os.path.join(project_path, 'project.yml')
        with open(project_yml_path) as open_file:
            project_yml = yaml.load(open_file)
            project_files = [f['path'] for f in project_yml['files']]
            assert 'sample.txt' in project_files

        # remove sample.txt
        args = cli.parse_args([
            '-w', workspace,
            '-p', str(project.project_root),
            '--remove', os.path.join(project.project_root, 'sample.txt'),
            '--debug'
        ])
        project = cli.dispatch(args)

        # check if NSD was removed
        with open(project_yml_path) as open_file:
            project_yml = yaml.load(open_file)
            project_files = [f['path'] for f in project_yml['files']]
            assert 'sample.txt' not in project_files
