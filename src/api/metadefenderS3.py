import boto3


class MetaDefenderS3:
    bucket_name = ""
    s3_client = ""
    
    def __init__(self, bucket):
        self.bucket_name = bucket    
        self.s3_client = boto3.client('s3')

    def tag_object(self, obj_key, new_tags):
        obj_tags = self.s3_client.get_object_tagging(Bucket=self.bucket_name, Key=obj_key)            

        tags = []   
        for tag in obj_tags['TagSet']:
            if tag['Key'] not in ["analysisTimestamp", "metaDefenderDataId", "metaDefenderResult"]:
                tags.append(tag)

        for key in new_tags:
            tags.append({"Key": key, "Value": new_tags[key]})
        
        self.s3_client.put_object_tagging(Bucket=self.bucket_name, Key=obj_key, Tagging={'TagSet': tags})


    def download_file(self, obj_key, download_path):
        self.s3_client.download_file(self.bucket_name, obj_key, download_path)

    def delete_file(self, filename):
        self.s3_client.delete_object(Bucket=self.bucket_name, Key=filename)