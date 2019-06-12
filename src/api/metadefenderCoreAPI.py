from botocore.vendored import requests
import datetime
import os
import json


class MetaDefenderCoreAPI:
    server_url = "http://localhost:8008"
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
            "endpoint": "/file/sanitized/"
        }
    }

    def __init__(self, url):
        self.server_url = url
    
    @property
    def supports_dowload_file(self):
        return False

    def submit_file(self, filename, filepath, analysis_callback_url):  
        json_response = {"error": "file not available"}   

        print("Submit file > filename:{0} @ path: {1}".format(filename, filepath))   

        with open(filepath, 'rb') as payload:
            print("file read successfully")   
            headers = {
                "filename": filename
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

        if "data_id" not in json_response:
            return {"error": json_response["error"]}

        data_id = json_response["data_id"]
        response = self.retrieve_result(data_id)
        payload = response.text

        # send all the details to the callback API 
        requests.request('post', analysis_callback_url, data=payload)

        return response.json()

    def retrieve_result(self, data_id):
        print("MetaDefender > Retrieve result for {0}".format(data_id))
        
        endpoint_details = self.api_endpoints["retrieve_result"]
        metadefender_url = self.server_url + endpoint_details["endpoint"].format(data_id=data_id)
        
        analysis_completed = False
        while (not analysis_completed):
            
            response = requests.request(endpoint_details["type"], metadefender_url)
            json_response = response.json()
            if ("process_info" in json_response and "progress_percentage" in json_response["process_info"]):
                analysis_completed = json_response["process_info"]["progress_percentage"] == 100
            else:
                print("Unexpected response from MetaDefender: {0}".format(response))
        
        return response


    def retrieve_sanitized_file(self, sanitized_file_url):
        return