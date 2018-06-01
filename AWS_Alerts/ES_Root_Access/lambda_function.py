from aws_requests_auth.boto_utils import BotoAWSRequestsAuth
from elasticsearch import Elasticsearch, RequestsHttpConnection
import time

def delete_index(index_name):
    es_client.indices.delete(index=index_name, ignore=[400, 404])

es_host = 'ES_ENDPOINT'
INDEX_NAME = ''

auth = BotoAWSRequestsAuth(aws_host=es_host,
             aws_region='eu-west-1',
             aws_service='es')


# use the requests connection_class and pass in our custom auth class
es_client = Elasticsearch(host=es_host,
                          port=80,
                          connection_class=RequestsHttpConnection,
                          http_auth=auth)

def lambda_handler (event, context):
    res = es_client.search(index=INDEX_NAME, body={
        "query" : {
      "constant_score" : { 
         "filter" : {
            "bool" : {
              "must" : [
                 { "match" : {"userIdentity.type":"Root"}},
                 { "term" : {"eventSource" : "iam.amazonaws.com"}}
              ],
              "must_not":[
                  {"term" : {"eventType" : "AwsServiceEvent"}},
                  #{ "exists" : { "field": "userIdentity.invokedBy" }}
              ],
              "filter":
              {
                "range": {
                  "eventTime": {
                    "gte":"now-15m",
                    "lte":"now"
                  }
                }
              }
            }
          }
      }
  }
        })
    print res

if __name__ == "__main__":
    lambda_handler(1,1)