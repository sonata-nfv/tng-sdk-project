import os
import oyaml as yaml
import copy


# generate 5GTANGO descriptors from the provided high-level arguments
def generate_descriptors(user_inputs, log):
    # load default descriptors (relative to file location, not curr directory)
    log.debug('Loading 5GTANGO default descriptors')
    descriptor_dir = os.path.join(os.path.dirname(__file__), os.pardir, 'default-descriptors')
    with open(os.path.join(descriptor_dir, 'tango_default_nsd.yml')) as f:
        tango_default_nsd = yaml.load(f)
    with open(os.path.join(descriptor_dir, 'tango_default_vnfd.yml')) as f:
        tango_default_vnfd = yaml.load(f)

    # generate VNFDs
    log.debug('Generating 5GTANGO VNFDs')
    vnfds = []
    tango_default_vnfd['author'] = user_inputs.author
    tango_default_vnfd['vendor'] = user_inputs.vendor
    for i in range(int(user_inputs.vnfs)):
        vnfd = copy.deepcopy(tango_default_vnfd)
        vnfd['name'] = 'default-vnf{}'.format(i)

        # add VNF image name if available
        if i < len(user_inputs.image_names):
            log.debug("VNF {} image name: {}"
                      .format(i, user_inputs.image_names[i]))
            vnfd['virtual_deployment_units'][0]['vm_image'] = \
                user_inputs.image_names[i]
        else:
            log.debug("Using default image name for VNF {}".format(i))
        # add VNF image name if available
        if i < len(user_inputs.image_types):
            log.debug("VNF {} image type: {}"
                      .format(i, user_inputs.image_types[i]))
            vnfd['virtual_deployment_units'][0]['vm_image_format'] = \
                user_inputs.image_types[i]
        else:
            log.debug("Using default image type for VNF {}".format(i))

        vnfds.append(vnfd)

    # generate NSD
    log.debug('Generating 5GTANGO NSD')
    nsd = tango_default_nsd
    nsd['author'] = user_inputs.author
    nsd['vendor'] = user_inputs.vendor
    nsd['name'] = user_inputs.name
    nsd['description'] = user_inputs.description

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

    # create descriptor dictionary
    descriptors = {'nsd': nsd, 'vnfds': vnfds}
    log.info('Generated 5GTANGO descriptors at {}'.format(user_inputs.out_path))
    return descriptors
