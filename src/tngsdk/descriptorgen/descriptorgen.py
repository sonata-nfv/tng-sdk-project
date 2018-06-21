import argparse
import oyaml as yaml        # ordered yaml to avoid reordering of descriptors
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

    # keep reusable parts of the default NSD that are independent from #VNFs
    # eg, there is always a mgmt vLink and a vLink from the input for vnf0
    # remove other stuff which will be replaced (vnf0-2-output vLink)
    del nsd['virtual_links'][2]
    del nsd['forwarding_graphs'][0]['constituent_virtual_links'][1]
    del nsd['forwarding_graphs'][0]['network_forwarding_paths'][0]['connection_points'][2:4]

    # now updated and extend the NSD
    for i, vnf in enumerate(vnfds):
        # list of involved VNFs
        # first entry already exists -> adjust, then append new ones
        if i > 0:
            nsd['network_functions'].append({})
        nsd['network_functions'][i]['vnf_id'] = 'vnf{}'.format(i)
        nsd['network_functions'][i]['vnf_name'] = vnf['name']
        nsd['network_functions'][i]['vnf_vendor'] = vnf['vendor']
        nsd['network_functions'][i]['vnf_version'] = vnf['version']

        # create corresponding vLinks
        # add vLink to next vnf
        if i < len(vnfds) - 1:
            nsd['virtual_links'].append({
                'id': 'vnf{}-2-vnf{}'.format(i, i+1),
                'connectivity_type': 'E-Line',
                'connection_points_reference': [
                    'vnf{}:output'.format(i), 'vnf{}:input'.format(i+1)
                ]
            })
        # for last vnf in chain, set vLink to output instead
        else:
            nsd['virtual_links'].append({
                'id': 'vnf{}-2-output'.format(i, i+1),
                'connectivity_type': 'E-Line',
                'connection_points_reference': [
                    'vnf{}:output'.format(i), 'output'
                ]
            })

        # add mgmt connection point (already exists for vnf0)
        if i > 0:
            nsd['virtual_links'][0]['connection_points_reference'].append(
                'vnf{}:mgmt'.format(i)
            )

    # adjust forwarding graph
    nsd['forwarding_graphs'][0]['number_of_virtual_links'] = len(vnfds) + 1
    # append new vLinks (skip mgmt and input-2-vnf0, which are already there)
    for i in range(2, len(nsd['virtual_links'])):
        nsd['forwarding_graphs'][0]['constituent_virtual_links'].append(
            nsd['virtual_links'][i]['id']
        )
    # append new vnfs
    for i in range(1, len(vnfds)):
        nsd['forwarding_graphs'][0]['constituent_vnfs'].append(
            nsd['network_functions'][i]['vnf_id']
        )

    # append in- and output of each vLink (keep input, vnf0:input, vnf0:output)
    pos = 3
    for i in range(2, len(nsd['virtual_links'])):
        nsd['forwarding_graphs'][0]['network_forwarding_paths'][0]['connection_points'].append({
            'connection_point_ref': nsd['virtual_links'][i]['connection_points_reference'][0],
            'position': pos
        })
        pos += 1
        nsd['forwarding_graphs'][0]['network_forwarding_paths'][0]['connection_points'].append({
            'connection_point_ref': nsd['virtual_links'][i]['connection_points_reference'][1],
            'position': pos
        })
        pos += 1

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
