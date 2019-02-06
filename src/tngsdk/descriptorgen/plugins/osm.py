import os
import oyaml as yaml
import copy


# generate OSM descriptors from the provided high-level arguments
def generate_descriptors(user_inputs, log):
    # load default descriptors (relative to file location, not curr directory)
    log.debug('Loading OSM default descriptors')
    descriptor_dir = os.path.join(os.path.dirname(__file__), os.pardir, 'default-descriptors')
    with open(os.path.join(descriptor_dir, 'osm_default_nsd.yml')) as f:
        osm_default_nsd = yaml.load(f)
    with open(os.path.join(descriptor_dir, 'osm_default_vnfd.yml')) as f:
        osm_default_vnfd = yaml.load(f)

    # generate VNFDs
    log.debug('Generating 5GTANGO VNFDs')
    vnfds = []
    for i in range(int(user_inputs.vnfs)):
        vnfd = copy.deepcopy(osm_default_vnfd)
        vnfd['vnfd-catalog']['vnfd'][0]['id'] = 'default-vnf{}'.format(i)
        vnfd['vnfd-catalog']['vnfd'][0]['name'] = 'default-vnf{}'.format(i)
        vnfd['vnfd-catalog']['vnfd'][0]['short-name'] = 'default-vnf{}'.format(i)
        vnfd['vnfd-catalog']['vnfd'][0]['vendor'] = user_inputs.vendor

        # add VNF image name and type if available
        if i < len(user_inputs.image_names):
            log.debug("VNF image {}: {}".format(i, user_inputs.image_names[i]))
            vnfd['vnfd-catalog']['vnfd'][0]['vdu'][0]['image'] = \
                user_inputs.image_names[i]
        else:
            log.debug("Using default image for VNF {}".format(i))

        vnfds.append(vnfd)

    # generate NSD
    log.debug('Generating 5GTANGO NSD')
    nsd = osm_default_nsd['nsd-catalog']['nsd'][0]
    nsd['vendor'] = user_inputs.vendor
    nsd['id'] = user_inputs.name
    nsd['name'] = user_inputs.name
    nsd['description'] = user_inputs.description

    # skip first vnf
    for i, vnf in enumerate(vnfds):
        # updated existing entries for vnf0 and then append new ones
        if i > 0:
            nsd['constituent-vnfd'].append({})
            nsd['vld'][0]['vnfd-connection-point-ref'].append({})

        # list involved vnfs
        nsd['constituent-vnfd'][i]['member-vnf-index'] = i
        nsd['constituent-vnfd'][i]['vnfd-id-ref'] = vnf['vnfd-catalog']['vnfd'][0]['id']

        # create mgmt connection points
        nsd['vld'][0]['vnfd-connection-point-ref'][i]['member-vnf-index-ref'] = i
        nsd['vld'][0]['vnfd-connection-point-ref'][i]['vnfd-connection-point-ref'] = 'mgmt'
        nsd['vld'][0]['vnfd-connection-point-ref'][i]['vnfd-id-ref'] = vnf['vnfd-catalog']['vnfd'][0]['id']

    # create vlinks between vnfs
    for i in range(len(vnfds)-1):
        nsd['vld'].append({
            'id': 'vnf{}-2-vnf{}'.format(i, i+1),
            'name': 'vnf{}-2-vnf{}'.format(i, i+1),
            'vnfd-connection-point-ref': [
                {
                    'member-vnf-index-ref': i,
                    'vnfd-connection-point-ref': 'output',
                    'vnfd-id-ref': vnfds[i]['vnfd-catalog']['vnfd'][0]['id']
                },
                {
                    'member-vnf-index-ref': i+1,
                    'vnfd-connection-point-ref': 'input',
                    'vnfd-id-ref': vnfds[i+1]['vnfd-catalog']['vnfd'][0]['id']
                }
            ]
        })

    # create descriptor dictionary
    descriptors = {'nsd': nsd, 'vnfds': vnfds}
    log.info('Generated OSM descriptors at {}'.format(user_inputs.out_path))
    return descriptors
