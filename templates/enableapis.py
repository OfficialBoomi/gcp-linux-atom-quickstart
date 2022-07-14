# Copyright 2020 Dell Boomi. All rights reserved.

""" This template enable GCP APIs. """

def generate_config(context):
    """ Entry point for the deployment resources. """

    resources = []
    for api in context.properties['apis']:

        resources.append(
            {
                'name': api['name'],
                'type': 'gcp-types/servicemanagement-v1:servicemanagement.services.enable',
                'properties': 
                    {
                        'consumerId': context.properties['consumerId'],
                        'serviceName': api['serviceName']
                    }
            }
        )


    return { 'resources': resources }
