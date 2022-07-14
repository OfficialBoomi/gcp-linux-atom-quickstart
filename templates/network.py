# Copyright 2020 Dell Boomi. All rights reserved.

""" This template creates a network, optionally with subnetworks. """

def generate_config(context):
    """ Entry point for the deployment resources. """

    deployment = context.env['deployment']
    name = context.properties.get('name') or context.env['name']
    network_self_link = '$(ref.{}.selfLink)'.format(name)
    auto_create_subnetworks = context.properties.get('autoCreateSubnetworks',False)
    

    resources = [
        {
            'type': 'compute.v1.network',
            'name': name,
            'properties':
                {
                    'name': name,
                    'autoCreateSubnetworks': auto_create_subnetworks
                }
        }
        
    ]

    # Subnetworks:
    out = {}
    for subnetwork in context.properties.get('subnetworks', []):
        subnetwork['network'] = network_self_link
        resources.append(
            {
                'name': subnetwork['name'],
                'type': 'subnetwork.py',
                'properties': subnetwork
            }
        )

        out[subnetwork['name']] = {
            'selfLink': '$(ref.{}.selfLink)'.format(subnetwork['name']),
            'ipCidrRange': '$(ref.{}.ipCidrRange)'.format(subnetwork['name']),
            'region': '$(ref.{}.region)'.format(subnetwork['name']),
            'network': '$(ref.{}.network)'.format(subnetwork['name']),
            'gatewayAddress': '$(ref.{}.gatewayAddress)'.format(
                subnetwork['name']
            )
        }

    return {
        'resources':
            resources,
        'outputs':
            [
                {
                    'name': 'vpcName',
                    'value': name
                },
                {
                    'name': 'selfLink',
                    'value': network_self_link
                },
                {
                    'name': 'subnetworks',
                    'value': out
                }
                
            ]
    }
