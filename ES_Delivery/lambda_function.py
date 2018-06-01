from elasticsearch import Elasticsearch, RequestsHttpConnection,helpers
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth
import datetime
import sys
from StringIO import StringIO
import gzip
import ast
import logging
import json


def setup_logging():
    logger = logging.getLogger()
    for h in logger.handlers:
      logger.removeHandler(h)
    
    h = logging.StreamHandler(sys.stdout)
    
    # use whatever format you want here
    FORMAT = '%(message)s'
    h.setFormatter(logging.Formatter(FORMAT))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)
    
    return logger

def lambda_handler (event, context):
    
    logger = setup_logging()
    
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
            "number_of_shards": 2,
            "number_of_replicas": 1
        }
    }

    INDEX_NAME = "cloudtrail-" + datetime.date.today().strftime("%Y.%m.%d")
    
    if ( es_client.indices.exists(index=INDEX_NAME) == False ):
        res = es_client.indices.create(index = INDEX_NAME, body = request_body)
        #print "Index Created"

    outEvent = str(event['awslogs']['data'])
    outEvent = gzip.GzipFile(fileobj=StringIO(outEvent.decode('base64','strict'))).read()
    outEvent = ast.literal_eval(outEvent)["logEvents"]

    actions = []
    for log in outEvent:
        log=json.loads(log["message"])
        log['_index']=INDEX_NAME
        log['_type']='Default'
        actions.append(log)
    
    helpers.bulk(es_client, actions, False)
    
    logger.info(json.dumps(es_client.count(index=INDEX_NAME)))
        
    return