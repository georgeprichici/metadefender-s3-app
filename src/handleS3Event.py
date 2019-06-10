import boto3
import os
import sys
import uuid
import urllib
from api.metadefenderS3 import MetaDefenderS3
from api.metadefenderCloudAPI import MetaDefenderCloudAPI
from api.metadefenderCoreAPI import MetaDefenderCoreAPI

def parse_event(event):
    return {
        "bucket": event['Records'][0]['s3']['bucket']['name'],
        "obj_key": urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
        
    }
     
def handler(event, context):
    obj_details = parse_event(event)
    
    bucket = obj_details["bucket"]
    obj_key = obj_details["obj_key"]
    download_path = '/tmp/{}{}'.format(uuid.uuid4(), obj_key)   
    
    metadefender_core_url = os.environ['MetaDefenderCoreURL']
    metadefender_cloud_apikey = os.environ['MetaDefenderCloudAPIkey']
    integration_type = os.environ['MetaDefenderDeployment']
    analysis_callback_url = os.environ['AnalysisComplateCallback']

    s3_client = MetaDefenderS3(bucket)
    s3_client.download_file(obj_key, download_path)

    metadefender_filename = "{0}::{1}".format(bucket, obj_key)
    md_api = MetaDefenderCoreAPI(metadefender_core_url) if (integration_type == "MetaDefenderCore") else MetaDefenderCloudAPI(metadefender_cloud_apikey)
    response = md_api.submit_file(metadefender_filename, download_path, analysis_callback_url)
    
    # s3_client.tag_object(obj_key, new_tags)
    return response

        # upload sanitized file
        #s3_client.upload_file(upload_path, '{}_sanitized'.format(bucket), key)