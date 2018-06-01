import boto3
import datetime
from elasticsearch import Elasticsearch, RequestsHttpConnection
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth

default_role_name = 'Security-Engineer'
inventory = {}
listed_roles = []

def lambda_handler (event, context):
    
    es_host = 'ES_ENDPOINT'

    auth = BotoAWSRequestsAuth(
        aws_host=es_host,
        aws_region='eu-west-1',
        aws_service='es'
    )

    # use the requests connection_class and pass in our custom auth class
    es_client = Elasticsearch(
        host=es_host,
        port=80,
        connection_class=RequestsHttpConnection,
        http_auth=auth
    )

    request_body = {
        "settings" : {
            "number_of_shards": 1,
            "number_of_replicas": 0
        }
    }

    INDEX_NAME = "awsinventory-" + datetime.date.today().strftime("%Y.%d.%m")
    
    if ( es_client.indices.exists(index=INDEX_NAME) == True ):
        es_client.indices.delete(index=INDEX_NAME, ignore=[400, 404])
        es_client.indices.create(index = INDEX_NAME, body = request_body)
        print "Index Restored"
    else:
        res = es_client.indices.create(index = INDEX_NAME, body = request_body)
        print "Index Created"

    sts_client = boto3.client('sts')
    assumedRoleObject = sts_client.assume_role(
        RoleArn='arn:aws:iam::828006401370:role/Security-AdministratorAccess',
        RoleSessionName='Security-AdministratorAccess')

    credentials = assumedRoleObject['Credentials']  

    iam_client = boto3.client('iam',
        aws_access_key_id = credentials['AccessKeyId'],
        aws_secret_access_key = credentials['SecretAccessKey'],
        aws_session_token = credentials['SessionToken'],)

    paginator = iam_client.get_paginator('list_role_policies')
    response_iterator = paginator.paginate(
        RoleName=default_role_name
    )

    for page in response_iterator:
        for policy_name in page['PolicyNames']:
            role_policy = iam_client.get_role_policy(
                RoleName=default_role_name,
                PolicyName=policy_name
            )
            listed_roles.extend([role_policy['PolicyDocument']['Statement']['Resource']])
        
    for role_arn in listed_roles:
        role_name = role_arn.split("/")[-1]
        account_name = role_name.rsplit('-', 1)[0]
        print "Account: %s" % account_name
        assumedRoleObject = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=role_name
        )
        credentials = assumedRoleObject['Credentials']

        inventory['AWS.account']=account_name
        inventory['Service']={}
        inventory['Service']['EC2'] = []
        inventory['Service']['ELB'] = []

        ec2_client = boto3.client(
            'ec2',
            aws_access_key_id = credentials['AccessKeyId'],
            aws_secret_access_key = credentials['SecretAccessKey'],
            aws_session_token = credentials['SessionToken'],
        )

        response = ec2_client.describe_instances()
        for instances in response['Reservations']:
            for instance in instances['Instances']:
                inventory['Service']['EC2'].extend([instance['InstanceId']])

        elb_client = boto3.client(
            'elb',
            aws_access_key_id = credentials['AccessKeyId'],
            aws_secret_access_key = credentials['SecretAccessKey'],
            aws_session_token = credentials['SessionToken'],
        )
        response = elb_client.describe_load_balancers()
        for elb in response['LoadBalancerDescriptions']:
            inventory['Service']['ELB'].extend([elb['LoadBalancerName']])
    
        res=es_client.index(index=INDEX_NAME, doc_type="Defect", body=inventory)
        print(res['result'])
        inventory.clear
    return

if __name__ == "__main__":
    lambda_handler(1,1)