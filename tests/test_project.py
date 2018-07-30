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

import os
import pytest
from tngsdk.project.workspace import Workspace
from tngsdk.project.project import Project


class TestProject:
    @pytest.fixture()
    def load_workspace(self):
        ws = Workspace.__create_from_descriptor__(Workspace.DEFAULT_WORKSPACE_DIR)
        assert ws
        return ws

    # create a new project 'test-project' inside pytest's tmpdir
    def test_project_creation(self, tmpdir):
        ws = self.load_workspace()

        # create a normal project (with sample files and folders)
        prj_path = os.path.join(tmpdir, 'test-project')
        project = Project(ws, prj_path)
        project.create_prj()
        assert os.path.isdir(prj_path)
        assert os.path.isfile(os.path.join(prj_path, 'project.yml'))

        return project

    # load the 'example-project' (part of the repo)
    def test_load_project(self):
        ws = self.load_workspace()
        prj_path = os.path.join('example-project')
        project = Project.__create_from_descriptor__(ws, prj_path)
        assert os.path.isdir(prj_path)
        assert os.path.isfile(os.path.join(prj_path, 'project.yml'))

    def test_add_file(self, tmpdir):
        project = self.test_project_creation(tmpdir)

        # create new text file inside the project
        file_path = os.path.join(project.project_root, 'sample.txt')
        with open(file_path, 'w') as f:
            f.write('sample text')
        assert os.path.isfile(file_path)

        # add to project.yml
        project.add_file(file_path)
        project_yml_path = os.path.join(project.project_root, 'project.yml')
        assert 'sample.txt' in open(project_yml_path).read()
