# Copyright 2020 Dell Boomi. All rights reserved.

""" This template creates a subnetwork. """

def generate_config(context):
    """ Entry point for the deployment resources. """

    name = context.properties.get('name', context.env['name'])
    required_properties = ['network', 'ipCidrRange', 'region']
    optional_properties = [
        'enableFlowLogs',
        'privateIpGoogleAccess',
        'secondaryIpRanges'
    ]

    # Load the mandatory properties, then the optional ones (if specified).
    properties = {p: context.properties[p] for p in required_properties}
    properties.update(
        {
            p: context.properties[p]
            for p in optional_properties
            if p in context.properties
        }
    )

    resources = [
        {
            'type': 'compute.v1.subnetwork',
            'name': name,
            'properties': properties
        }
    ]

    output = [
        {
            'name': 'name',
            'value': name
        },
        {
            'name': 'selfLink',
            'value': '$(ref.{}.selfLink)'.format(name)
        },
        {
            'name': 'ipCidrRange',
            'value': '$(ref.{}.ipCidrRange)'.format(name)
        },
        {
            'name': 'region',
            'value': '$(ref.{}.region)'.format(name)
        },
        {
            'name': 'network',
            'value': '$(ref.{}.network)'.format(name)
        },
        {
            'name': 'gatewayAddress',
            'value': '$(ref.{}.gatewayAddress)'.format(name)
        }
    ]

    return {'resources': resources, 'outputs': output}
