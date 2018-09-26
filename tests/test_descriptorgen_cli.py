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
import tngsdk.descriptorgen.descriptorgen as cli


class TestDescriptorgenCLI:
    # generate descriptors with custom author, vendor, name, description
    def test_generate_custom_descriptors(self):
        args = cli.parse_args([
            '--author', 'test.author',
            '--vendor', 'test.vendor',
            '--name', 'test.service',
            '--description', 'test.description',
            '-o', 'test-descriptorgen'
        ])
        cli.generate(args)

        # check tango nsd and vnfd
        with open(os.path.join('test-descriptorgen', 'tango_nsd.yml'), 'r') as f:
            tango_nsd = yaml.load(f)
            assert tango_nsd['author'] == 'test.author'
            assert tango_nsd['vendor'] == 'test.vendor'
            assert tango_nsd['name'] == 'test.service'
            assert tango_nsd['description'] == 'test.description'
            assert len(tango_nsd['network_functions']) == 1

        with open(os.path.join('test-descriptorgen', 'tango_vnfd0.yml'), 'r') as f:
            tango_vnfd = yaml.load(f)
            assert tango_vnfd['author'] == 'test.author'
            assert tango_vnfd['vendor'] == 'test.vendor'

        # check osm nsd and vnfd
        with open(os.path.join('test-descriptorgen', 'osm_nsd.yml'), 'r') as f:
            osm_nsd = yaml.load(f)
            assert osm_nsd['vendor'] == 'test.vendor'
            assert osm_nsd['id'] == 'test.service'
            assert osm_nsd['name'] == 'test.service'
            assert osm_nsd['description'] == 'test.description'
            assert len(osm_nsd['constituent-vnfd']) == 1

        with open(os.path.join('test-descriptorgen', 'osm_vnfd0.yml'), 'r') as f:
            osm_vnfd = yaml.load(f)
            assert osm_vnfd['vnfd-catalog']['vnfd'][0]['vendor'] == 'test.vendor'

        # clean up: remove test folder again
        shutil.rmtree('test-descriptorgen')

    # generate descriptors for service with multiple vnfs
    @pytest.mark.parametrize('num_vnfs', [(2), (3), (4)])
    def test_generate_multiple_descriptors(self, num_vnfs):
        args = cli.parse_args([
            '--vnfs', str(num_vnfs),
            '-o', 'test-descriptorgen'
        ])
        cli.generate(args)

        # check the NSDs
        with open(os.path.join('test-descriptorgen', 'tango_nsd.yml'), 'r') as f:
            tango_nsd = yaml.load(f)
            assert len(tango_nsd['network_functions']) == num_vnfs

        with open(os.path.join('test-descriptorgen', 'osm_nsd.yml'), 'r') as f:
            osm_nsd = yaml.load(f)
            assert len(osm_nsd['constituent-vnfd']) == num_vnfs

        # check all vnfd files exist
        for i in range(0, num_vnfs):
            assert os.path.isfile(os.path.join('test-descriptorgen', 'tango_vnfd{}.yml'.format(i)))
            assert os.path.isfile(os.path.join('test-descriptorgen', 'osm_vnfd{}.yml'.format(i)))

        shutil.rmtree('test-descriptorgen')

    # generate only tango descriptors
    def test_generate_tango_descriptors(self):
        args = cli.parse_args([
            '--tango',
            '-o', 'test-descriptorgen'
        ])
        cli.generate(args)

        assert os.path.isfile(os.path.join('test-descriptorgen', 'tango_nsd.yml'))
        assert os.path.isfile(os.path.join('test-descriptorgen', 'tango_vnfd0.yml'))
        assert not os.path.isfile(os.path.join('test-descriptorgen', 'osm_nsd.yml'))
        assert not os.path.isfile(os.path.join('test-descriptorgen', 'osm_vnfd0.yml'))

        shutil.rmtree('test-descriptorgen')

    # generate only osm descriptors
    def test_generate_osm_descriptors(self):
        args = cli.parse_args([
            '--osm',
            '-o', 'test-descriptorgen'
        ])
        cli.generate(args)

        assert os.path.isfile(os.path.join('test-descriptorgen', 'osm_nsd.yml'))
        assert os.path.isfile(os.path.join('test-descriptorgen', 'osm_vnfd0.yml'))
        assert not os.path.isfile(os.path.join('test-descriptorgen', 'tango_nsd.yml'))
        assert not os.path.isfile(os.path.join('test-descriptorgen', 'tango_vnfd0.yml'))

        shutil.rmtree('test-descriptorgen')
