# Copyright 2020 Dell Boomi. All rights reserved.

""" This template creates a CloudFunction. """
URL_BASE = 'https://www.googleapis.com/compute/v1/projects/'


def generate_config(context):
    """ Entry point for the deployment resources. """

    name = context.properties.get('name', context.env['name'])    
    region = context.properties['region']
    deployment = context.env['deployment']
    instance_template = deployment + '-it'
    igm = deployment + '-igm'         
    bucketname = deployment + '-bucket'

    if context.properties['boomiAuthenticationType'].upper()=="TOKEN" :
        boomiUserEmailID= "BOOMI_TOKEN." +context.properties['boomiUserEmailID']
    else : 
        boomiUserEmailID= context.properties['boomiUserEmailID']  
    
    resources = []
    resources.append(
       {
            'name': 'CreateBucket',
            'type': 'gcp-types/storage-v1:buckets',
            'properties':
                {
                   "name" : bucketname,
                   "locationtype" : "Region",
                   "location" : region,                  
                   "storageClass" : "Standard"                                                          
                                                                    
                }
        }

    )   
    resources.append(
            {
            'name': 'Cloudbuild',
            'type': 'cloudbuild.jinja',
            'properties': 
                  {
                    'bucketname' : bucketname

                  },
            'metadata': {      'dependsOn': ['CreateBucket']
                     }
            }
        )
    resources.append(
       {
            'name': 'createfunction',
            'type': 'gcp-types/cloudfunctions-v1:projects.locations.functions',
            'properties':
                {
                    'function': name +"licensevalidation",        
                    'parent': "projects/"+context.properties.get('project', context.env['project'])+"/locations/"+context.properties['region'],
                    'sourceArchiveUrl': 'gs://'+bucketname+'/License_validation.zip',
                    'entryPoint':'handler',
                    'httpsTrigger': {"url": "https://"+context.properties['region']+"-"+context.properties.get('project', context.env['project'])+"/"+name+"licensevalidation","securityLevel": "SECURE_ALWAYS"},
                    'timeout': '60s',
                    'serviceAccountEmail' :context.properties['serviceAccountEmail'],
                    'availableMemoryMb': 256 ,
                    'runtime': 'python37'
                                                      
                },
            'metadata': { 'dependsOn': [deployment+'-cloudbuild']
                     }
        }

    )
    callfunction ={
         'type': 'gcp-types/cloudfunctions-v1:cloudfunctions.projects.locations.functions.call',
         'name': 'callfunction',
         'properties':
                {
                 'name':"projects/"+context.properties.get('project', context.env['project'])+"/locations/" +context.properties['region']+"/functions/"+name +"licensevalidation",

                 'data': '{"BoomiUsername":"'+boomiUserEmailID+'","boomiAuthenticationType":"'+context.properties['boomiAuthenticationType']+'","BoomiPassword":"'+context.properties['boomiPassword']+'","BoomiAccountID":"'+context.properties['boomiAccountID']+'","TokenType":"atom","TokenTimeout":"60", "bucketname": "'+bucketname+'"}'

                },

         'metadata': {
                'dependsOn': ['createfunction']
                     }
          }   
    resources.append(callfunction)  
    resources.append(

       {

            # Create the Instance Template

          'name': instance_template,

          'type': 'compute.v1.instanceTemplate',

          'properties': {

              'properties': {

                  'serviceAccounts': [{

                      'email':

                          context.properties['serviceAccountEmail'],

                      'scopes':

                          context.properties['serviceAccountScopes']

                  }],

                  'tags': context.properties['tags'],

                  'machineType':

                      context.properties['machineType'],

                  'networkInterfaces': [{

                      'network':

                          context.properties['network'],

                      'subnetwork':

                          context.properties['publicSubnet'],

                      'accessConfigs': [{

                          'name': 'External NAT',

                          'type': 'ONE_TO_ONE_NAT'

                      }]

                  }],

                  'metadata': {

                      'items': [{

                          'key': 'startup-script',

                          'value': context.properties['startupScript']

                        }]

                  },

                  'disks': [{

                      'deviceName': 'boot',

                      'type': 'PERSISTENT',

                      'boot': True,

                      'autoDelete': False,

                      'diskType': 'pd-ssd',

                      'diskSizeGb': '30',

                      'mode': 'READ_WRITE',

                      'initializeParams': {

                          'sourceImage':

                              URL_BASE +

                              context.properties['machineImage']

                      }

                  }]

              }

          },

           'metadata': {

               'dependsOn': ['callfunction']

        }

       }

       )

    resources.append(

       {

          # Instance Group Manager

          'name': igm,

          'type': 'compute.v1.regionInstanceGroupManager',

          'properties': {

              'region': region,

              'failoverAction': 'NO_FAILOVER',

              'baseInstanceName': deployment + '-instance',

              'instanceTemplate': '$(ref.' + instance_template + '.selfLink)',

              'targetSize': 1

          },

          'metadata': {

               'dependsOn': ['callfunction']

        }

       }

       )

   

    return{
        'resources': resources        

    }
