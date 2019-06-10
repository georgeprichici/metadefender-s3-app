# metadefender-s3-app

## Summary

This is a sample template for metadefender-s3-app:
- Analyze all new files uploaded to an S3 bucket with MetaDefender Cloud or Core
- S3 event is triggered when a file is uploaded to the S3 bucket, which will call the handleS3Event.handler
  - based on the env params provided when launching the CloudFormation script, the new file will be submitted to either MetaDefender Cloud or a local (in your environment) deployment of MetaDefender 
- When analysis is complete a callback is made, which will call analysisCallback.handler
  - Based on the result and the selected remediation type, the file can be:
    - Tagged: each file will be tagged with:
      - metaDefenderDataId
      - analysisTimestamp
      - metaDefenderResult
    - Deleted: for all infected files
    - Sanitized: not yet implemented
- Alerting is also available for all infected files detected:
  - SNS integration available, a new topic will be created
  - user should subscribe to the topic

## Deploy in AWS

### CloudFormation

* Create a new Stack in CloudFormation
   * Upload the provided CloudFormation template (packaged version after you call ``` sam package ``` command
   * Fill the form with the requirement details:
      * <img src="https://md-test-doc.s3-us-west-2.amazonaws.com/metadefender-s3-cloudformation-form.png" width="50%" height="50%"> 
      * Select which deployment you would like to use (Cloud or Core)
      * Provide the MetaDefender Cloud APIkey or the location of the MetaDefender Core instance
         * For MetaDefender Cloud APIkey go to https://metadefender.opswat.com, register and you will be able to retrieve the APIkey from your profile
   * Go through the wizzard and create the Stack
* Map the S3 bucket Event to the new Lambda function
   * Go to your bucket Properties section and select Events
   *  <img src="https://md-test-doc.s3-us-west-2.amazonaws.com/metadefender-s3-bucket-event-setup.png" width="50%" height="50%">
   * Select Lambda function and then MetaDefenderSubmitFilesFunction to handle all the `ObjectCreation` events
* Upload the `eicar file` to test the detection 
   * The current selection for remediation is Tag only:
   * <img src="https://md-test-doc.s3-us-west-2.amazonaws.com/metadefender-s3-bucket-tags.png" width="50%" height="50%"> 
   
* Notification of infected file can also be sent via SNS (in this case email subscription was enabled):
   * <img src="https://md-test-doc.s3-us-west-2.amazonaws.com/metadefender-sns-notif.png" width="50%" height="50%"> 

## Code structure

```bash
.
├── README.md                      <-- This instructions file
├── src                            <-- Source code for a lambda function
│   ├── __init__.py
│   ├── analysisCallback.py        <-- Lambda function responsible of handling the callback from MetaDefender
│   ├── handleS3Event.py           <-- Labmbda function which will submit to MetaDefender all the new uploaded files to any attached S3 bucket
│   └── api                     
│       ├── metadefenderCloud.py   <-- MetaDefender Cloud integration for the file API
│       ├── metedefenderCore.py    <-- MetaDefender Core integration for the file API
│       └── metedefenderS3.py      <-- S3 properties handling (tagging, delete, put, etc.)
├── metadefender-s3-template.yaml  <-- SAM Template
└── tests                          <-- Unit tests (not available)
    ├── event.json
    ├── s3-event.json
    └── unit
        ├── __init__.py
        └── test_handler.py
```

## Requirements

* AWS CLI already configured with Administrator permission
* [Python 3 installed](https://www.python.org/downloads/)
* [Docker installed](https://www.docker.com/community-edition)

## Setup process

### Local development

**Invoking function locally using a local sample payload**

```bash
sam local invoke MetaDefenderSubmitFileFunction --event ./tests/s3-event.json
```

**Invoking function locally through local API Gateway**

```bash
sam local start-api
```

If the previous command ran successfully you should now be able to hit the following local endpoint to invoke your function `http://localhost:3000/callback`

**SAM CLI** is used to emulate both Lambda and API Gateway locally and uses our `metadefender-s3-template.yaml` to understand how to bootstrap this environment (runtime, where the source code is, etc.) - The following excerpt is what the CLI will read in order to initialize an API and its routes:

```yaml
...
Events:
    AnalysisCallbackFunction:
        Type: Api # More info about API Event Source: https://github.com/awslabs/serverless-application-model/blob/master/versions/2016-10-31.md#api
          Properties:
            Path: /callback
            Method: post
```

## Packaging and deployment

AWS Lambda Python runtime requires a flat folder with all dependencies including the application. SAM will use `CodeUri` property to know where to look up for both application and dependencies:

```yaml
...
    MetaDefenderSubmitFileFunction:
      Type: AWS::Serverless::Function
      Properties:
        FunctionName: MetaDefenderSubmitFileFunction
        Description: Analyze all new files submitted to defined S3 bucket with MetaDefender
        CodeUri: src/
            ...
```

Firstly, we need a `S3 bucket` where we can upload our Lambda functions packaged as ZIP before we deploy anything - If you don't have a S3 bucket to store code artifacts then this is a good time to create one:

```bash
aws s3 mb s3://BUCKET_NAME
```

Next, run the following command to package our Lambda function to S3:

```bash
sam package 
    --template-file metadefender-s3-template.yaml 
    --output-template-file packaged.yaml  
    --s3-bucket REPLACE_THIS_WITH_YOUR_S3_BUCKET_NAME
```

Next, the following command will create a Cloudformation Stack and deploy your SAM resources.

```bash
sam deploy \
    --template-file packaged.yaml \
    --stack-name metadefender-s3-app \
    --capabilities CAPABILITY_IAM
```

> **See [Serverless Application Model (SAM) HOWTO Guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-quick-start.html) for more details in how to get started.**

After deployment is complete you can run the following command to retrieve the API Gateway Endpoint URL:

```bash
aws cloudformation describe-stacks \
    --stack-name metadefender-s3-app \
    --query 'Stacks[].Outputs[?OutputKey==`AnalysisCallbackAPI`]' \
    --output table
``` 

## Fetch, tail, and filter Lambda function logs

To simplify troubleshooting, SAM CLI has a command called sam logs. sam logs lets you fetch logs generated by your Lambda function from the command line. In addition to printing the logs on the terminal, this command has several nifty features to help you quickly find the bug.

`NOTE`: This command works for all AWS Lambda functions; not just the ones you deploy using SAM.

```bash
sam logs -n MetaDefenderSubmitFileFunction --stack-name metadefender-s3-app --tail
```

You can find more information and examples about filtering Lambda function logs in the [SAM CLI Documentation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-logging.html).

## Testing


Next, we install test dependencies and we run `pytest` against our `tests` folder to run our initial unit tests:

```bash
pip install pytest pytest-mock --user
python -m pytest tests/ -v
```

## Cleanup

In order to delete our Serverless Application recently deployed you can use the following AWS CLI Command:

```bash
aws cloudformation delete-stack --stack-name metadefender-s3-app
```

## Bringing to the next level

Here are a few things you can try to get more acquainted with building serverless applications using SAM:

### Learn how SAM Build can help you with dependencies

* Uncomment lines on `app.py`
* Build the project with ``sam build --use-container``
* Invoke with ``sam local invoke MetaDefenderSubmitFileFunction --event s3-event.json``
* Update tests

### Create an additional API resource

* Create a catch all resource (e.g. /hello/{proxy+}) and return the name requested through this new path
* Update tests

### Step-through debugging

* **[Enable step-through debugging docs for supported runtimes]((https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-using-debugging.html))**

Next, you can use AWS Serverless Application Repository to deploy ready to use Apps that go beyond hello world samples and learn how authors developed their applications: [AWS Serverless Application Repository main page](https://aws.amazon.com/serverless/serverlessrepo/)

# Appendix

## Building the project

[AWS Lambda requires a flat folder](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html) with the application as well as its dependencies in  deployment package. When you make changes to your source code or dependency manifest,
run the following command to build your project local testing and deployment:

```bash
sam build
```

If your dependencies contain native modules that need to be compiled specifically for the operating system running on AWS Lambda, use this command to build inside a Lambda-like Docker container instead:
```bash
sam build --use-container
```

By default, this command writes built artifacts to `.aws-sam/build` folder.

## SAM and AWS CLI commands

All commands used throughout this document

```bash
# Generate event.json via generate-event command
sam local generate-event apigateway aws-proxy > event.json

# Invoke function locally with event.json as an input
sam local invoke MetaDefenderSubmitFileFunction --event s3-event.json

# Run API Gateway locally
sam local start-api

# Create S3 bucket
aws s3 mb s3://BUCKET_NAME

# Package Lambda function defined locally and upload to S3 as an artifact
sam package \
    --output-template-file packaged.yaml \
    --s3-bucket REPLACE_THIS_WITH_YOUR_S3_BUCKET_NAME

# Deploy SAM template as a CloudFormation stack
sam deploy \
    --template-file packaged.yaml \
    --stack-name metadefender-s3-app \
    --capabilities CAPABILITY_IAM

# Describe Output section of CloudFormation stack previously created
aws cloudformation describe-stacks \
    --stack-name metadefender-s3-app \
    --query 'Stacks[].Outputs[?OutputKey==`AnalysisCallbackAPI`]' \
    --output table

# Tail Lambda function Logs using Logical name defined in SAM Template
sam logs -n MetaDefenderSubmitFileFunction --stack-name metadefender-s3-app --tail
```

