from botocore.vendored import requests
import datetime
import os
import json


class MetaDefenderCloudAPI:
    server_url = "https://api.metadefender.com/v4"
    apikey = ""

    api_endpoints = {
        "submit_file": {
            "type": "post",
            "endpoint": "/file"
        },
        "retrieve_result": {
            "type": "get",
            "endpoint": "/file/{data_id}"
        },
        "sanitized_file": {
            "type": "get",
            "endpoint": "/file/converted/{data_id}"
        }
    }

    def __init__(self, apikey=""):
        self.apikey = apikey

    def submit_file(self, filename, filepath, analysis_callback_url):  
        json_response = {"error": "file not available"}   

        print("Submit file > filename:{0} @ path: {1}".format(filename, filepath))   

        with open(filepath, 'rb') as payload:
                print("file read successfully")   
                headers = {
                    "filename": filename,
                    "callbackurl": analysis_callback_url,
                    "apikey": self.apikey,
                    "content-type": "application/octet-stream"
                }
                before_submission = datetime.datetime.now()                
                endpoint_details = self.api_endpoints["submit_file"]
                metadefender_url = self.server_url + endpoint_details["endpoint"]

                print("File sent to MetaDefender")   
                response = requests.request(endpoint_details["type"], metadefender_url, data=payload, headers=headers, timeout=(2,30))
                json_response = json.loads(response.text)
                
                print("MetaDefender response: {0}".format(json_response))   

                http_status = response.status_code                           
                total_submission_time = datetime.datetime.now() - before_submission

                print("{timestamp} {name} >> time: {total_time}, http status: {status}, response: {id}".format(timestamp=before_submission, name=filename, total_time=total_submission_time, status=http_status, id=response.text))                

                json_response["status"] = "ok" if ('data_id' in json_response) else "failed"
        return json_response


    def retrieve_sanitized_file(self, sanitized_file_url):
        return