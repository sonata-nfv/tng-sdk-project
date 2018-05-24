import argparse
import yaml
import copy
from os import path


def parse_args():
    parser = argparse.ArgumentParser(description='Generate NSD and VNFDs')
    parser.add_argument('--author', help='set a specific NSD and VNFD author',
                        required=False, default='Tango', dest='author')
    parser.add_argument('--vendor', help='set a specific NSD and VNFD vendor',
                        required=False, default='Tango', dest='vendor')
    parser.add_argument('--name', help='set a specific NSD name',
                        required=False, default='tango-nsd', dest='name')
    parser.add_argument('--description', help='set a specific NSD description',
                        required=False, default='Default description',
                        dest='description')
    parser.add_argument('--vnfs', help='set a specific number of VNFs',
                        required=False, default=1, dest='vnfs')

    return parser.parse_args()


def generate_tango():
    args = parse_args()

    # load default descriptors (relative to file location, not curr directory)
    descriptor_dir = path.join(path.dirname(__file__), 'default-descriptors')
    with open(path.join(descriptor_dir, 'tango_default_nsd.yml')) as f:
        tango_default_nsd = yaml.load(f)
    with open(path.join(descriptor_dir, 'tango_default_vnfd.yml')) as f:
        tango_default_vnfd = yaml.load(f)

    # generate VNFDs
    vnfds = []
    tango_default_vnfd['author'] = args.author
    tango_default_vnfd['vendor'] = args.vendor
    for i in range(int(args.vnfs)):
        vnfd = copy.deepcopy(tango_default_vnfd)
        vnfd['name'] = 'default-vnf{}'.format(i)
        vnfds.append(vnfd)

    # generate NSD
    nsd = tango_default_nsd
    nsd['author'] = args.author
    nsd['vendor'] = args.vendor
    nsd['name'] = args.name
    nsd['description'] = args.description

    for i, vnf in enumerate(vnfds):
        # list involved VNFs
        # first entry already exists -> adjust, then append new ones
        if i > 0:
            nsd['network_functions'].append({})
        nsd['network_functions'][i]['vnf_id'] = 'vnf{}'.format(i)
        nsd['network_functions'][i]['vnf_name'] = vnf['name']
        nsd['network_functions'][i]['vnf_vendor'] = vnf['vendor']
        nsd['network_functions'][i]['vnf_version'] = vnf['version']

        # TODO: vLinks, forwarding graph (see javascript implementation)

    return nsd, vnfds


def generate():
    nsd, vnfds = generate_tango()
    # TODO: generate OSM

    # write generated descriptors to file
    # TODO: allow to set location (-o); or just return the yaml without saving
    with open('tango_nsd.yml', 'w', newline='') as f:
        yaml.dump(nsd, f, default_flow_style=False)
    for i, vnf in enumerate(vnfds):
        filename = 'tango_vnfd{}.yml'.format(i)
        with open(filename, 'w', newline='') as f:
            yaml.dump(vnf, f, default_flow_style=False)


if __name__ == '__main__':
    generate()
