# Copyright 2020 Dell Boomi. All rights reserved.

""" This template creates an IAM policy member. """


def generate_config(context):
    """ Entry point for the deployment resources. """

    project_id = context.properties.get('projectId', context.env['project'])

    resources = []
    for ii, role in  enumerate(context.properties['roles']):
        for i, member in enumerate(role['members']):
            policy_get_name = 'get-iam-policy-{}-{}-{}'.format(context.env['name'], ii, i)

            resources.append(
                {
                    'name': policy_get_name,
                    'type': 'gcp-types/cloudresourcemanager-v1:virtual.projects.iamMemberBinding',
                    'properties':
                    {
                        'resource': project_id,
                        'role': role['role'],
                        'member': member
                    }
                }
            )

    return {"resources": resources}
