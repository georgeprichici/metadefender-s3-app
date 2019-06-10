import json
import os
import boto3
from api.metadefenderS3 import MetaDefenderS3

def tag_files(bucket, filename, analysis_results):

    new_tags = {
        "analysisTimestamp": analysis_results["file_info"]["upload_timestamp"],
        "metaDefenderDataId": analysis_results["data_id"],
        "metaDefenderResult": analysis_results["process_info"]["result"]
    }
    
    s3_client = MetaDefenderS3(bucket)
    s3_client.tag_object(filename, new_tags)

    return new_tags


def delete_files(bucket, filename, analysis_results):

    
    if (analysis_results["process_info"]["result"] != "Allowed"):
        s3_client = MetaDefenderS3(bucket)
        s3_client.delete_file(filename)

    return {"status": "done", "message": "file {0} deleted".format(filename)}

def check_bucket_versioning(bucket_name, enable_versioning):
    s3_client = boto3.client('s3')
    bucket_versioning = s3_client.BucketVersioning(bucket_name)

    if bucket_versioning != "Enabled" and enable_versioning:
        s3_client.enable()

def replace_with_sanitized(bucket_name, filename, analysis_results):

    return True

def handler(event, context):
    response = json.loads(event["body"])

    if "data_id" not in response:
        return {"error": response["error"]}

    data_id = response["data_id"]
    full_name = response["file_info"]["display_name"]
    
    bucket, filename = full_name.split("::")
    print("Received callback for file: {0} (data_id: {1}".format(filename, data_id))


    remediation_type = os.environ['RemediationType']
    report_infected = os.environ['ReportInfectedFiles']
    override_sanitized = os.environ['EnableBucketVersioning']
    sns_topic = os.environ['SNSTopic']

    remediation_dict = {
        "Tag": tag_files, 
        "Delete": delete_files, 
        "Sanitize": replace_with_sanitized
    }

    if report_infected == "true":
        report_analysis_status(sns_topic, full_name, response, remediation_type)

    if override_sanitized == "true":
        check_bucket_versioning(bucket, override_sanitized == "true")   

    if remediation_type in remediation_dict:
        print("Remediate using method: {0}".format(remediation_type))
        remediation = remediation_dict[remediation_type]
        response = remediation(bucket, filename, response)

    
    return response

def report_analysis_status(sns_topic, filename, analysis_result, remediation):
    verdict = analysis_result["process_info"]["result"]

    subject = "MetaDefender > {0}: {1}".format(filename, verdict)
    message = "MetaDefender Analysis: {0} was {1} and handled as {2}\n\nScan report:\n{3}".format(filename, verdict, remediation, json.dumps(analysis_result["scan_results"],indent=3))
    
    sns = boto3.client('sns')
    response = sns.publish(TopicArn=sns_topic, Message=message, Subject=subject)

    return response
        
        
