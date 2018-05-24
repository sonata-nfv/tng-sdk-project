import argparse
import yaml
import copy


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

    with open('default-descriptors/tango_default_nsd.yml') as f:
        tango_default_nsd = yaml.load(f)
    with open('default-descriptors/tango_default_vnfd.yml') as f:
        tango_default_vnfd = yaml.load(f)

    # generate VNFDs
    vnfds = []
    tango_default_vnfd['author'] = args.author
    tango_default_vnfd['vendor'] = args.vendor
    for i in range(args.vnfs):
        vnfd = copy.deepcopy(tango_default_vnfd)
        vnfd['name'] = 'default-vnf{}'.format(i)
        vnfds.append(vnfd)

    # generate NSD
    nsd = tango_default_nsd
    nsd['author'] = args.author
    nsd['vendor'] = args.vendor
    nsd['name'] = args.name
    nsd['description'] = args.description

    # TODO: vLinks, forwarding graph

    return nsd, vnfds


def generate():
    nsd, vnfds = generate_tango()
    # TODO: generate OSM

    # write generated descriptors to file
    # TODO: allow to specify location. or just return the yaml without saving
    with open('tango_nsd.yml', 'w', newline='') as f:
        yaml.dump(nsd, f, default_flow_style=False)
    for i, vnf in enumerate(vnfds):
        filename = 'tango_vnfd{}.yml'.format(i)
        with open(filename, 'w', newline='') as f:
            yaml.dump(vnf, f, default_flow_style=False)


if __name__ == '__main__':
    generate()
