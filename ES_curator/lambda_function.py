from aws_requests_auth.boto_utils import BotoAWSRequestsAuth
from elasticsearch import Elasticsearch, RequestsHttpConnection
import time

def delete_index(index_name):
    es_client.indices.delete(index=index_name, ignore=[400, 404])

es_host = 'ES_ENDPOINT'

auth = BotoAWSRequestsAuth(aws_host=es_host,
             aws_region='eu-west-1',
             aws_service='es')


# use the requests connection_class and pass in our custom auth class
es_client = Elasticsearch(host=es_host,
                          port=80,
                          connection_class=RequestsHttpConnection,
                          http_auth=auth)

def lambda_handler (event, context):
    indices=es_client.indices.get_settings("*")

    current_milli_time = lambda: int(round(time.time() * 1000))
    _7_days_back = current_milli_time()-604800000

    for key in indices:
        index_creation_date = indices[key]['settings']['index']['creation_date']
        if index_creation_date < _7_days_back:
            delete_index(key)
    return

if __name__ == "__main__":
    lambda_handler(1,1)