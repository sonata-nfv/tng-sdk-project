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


import argparse
import oyaml as yaml        # ordered yaml to avoid reordering of descriptors
import os
import logging
import coloredlogs
import sys
from tngsdk.descriptorgen.plugins import tango, osm


log = logging.getLogger(__name__)


def parse_args(input_args=None):
    parser = argparse.ArgumentParser(description='Generate NSD and VNFDs',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-o', help='set relative output path',
                        required=False, default='.', dest='out_path')
    parser.add_argument('--debug', help='increases logging level to debug',
                        required=False, action='store_true')
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
                        required=False, default=1, dest='vnfs')

    if input_args is None:
        input_args = sys.argv[1:]
    return parser.parse_args(input_args)


# save the generated descriptors in the specified folder; add a prefix for each flavor
def save_descriptors(nsd, vnfds, flavor, folder='.'):
    # create dir if it doesn't exist
    if not os.path.exists(folder):
        os.makedirs(folder)

    # dump generated nsd and vnfds
    outfile = os.path.join(folder, '{}_nsd.yml'.format(flavor))
    with open(outfile, 'w', newline='') as f:
        yaml.dump(nsd, f, default_flow_style=False)
    for i, vnf in enumerate(vnfds):
        outfile = os.path.join(folder, '{}_vnfd{}.yml'.format(flavor, i))
        with open(outfile, 'w', newline='') as f:
            yaml.dump(vnf, f, default_flow_style=False)


def generate(args=None):
    if args is None:
        args = parse_args()

    if args.debug:
        coloredlogs.install(level='DEBUG')
    else:
        coloredlogs.install(level='INFO')

    # generate and save tango descriptors
    if not args.osm:
        descriptors = tango.generate_descriptors(args, log)
        save_descriptors(descriptors['nsd'], descriptors['vnfds'], 'tango', args.out_path)

    # generate and save osm descriptors
    if not args.tango:
        descriptors = osm.generate_descriptors(args, log)
        save_descriptors(descriptors['nsd'], descriptors['vnfds'], 'osm', args.out_path)


if __name__ == '__main__':
    generate()
