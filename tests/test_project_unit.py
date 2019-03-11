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
import tngsdk.project.workspace as workspace
from tngsdk.project.workspace import Workspace
from tngsdk.project.project import Project


class TestProjectUnit:

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

    # test descriptors of project 'example-project'    
    def test_example_project_descriptors(self, workspace):
        ws = Workspace.load_workspace(workspace)
        example_project = Project.load_project('example-project', workspace=ws)
        example_project.status()
        
        vnfds = example_project.get_vnfds()
        assert vnfds == ['tango_vnfd0.yml']

        nsds = example_project.get_nsds()
        assert nsds == ['tango_nsd.yml']

        tstds = example_project.get_tstds()
        assert tstds == ['test-descriptor-example.yml']
