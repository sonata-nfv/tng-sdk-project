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


import oyaml as yaml        # ordered yaml to avoid reordering of descriptors
import os
import logging
import coloredlogs
from tngsdk import cli
from tngsdk.descriptorgen.plugins import tango, osm

log = logging.getLogger(__name__)


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
        args = cli.parse_args()

    if args.debug:
        coloredlogs.install(level='DEBUG')
    else:
        coloredlogs.install(level='INFO')

    log.info("Generating descriptors with args {}".format(args))

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
