import logging
import subprocess
import xml.etree.ElementTree as ET
import boto3
import os 
import json
import uuid

S3 = boto3.client("s3")
LOGGER = logging.getLogger('boto3')
LOGGER.setLevel(logging.INFO)
REGION = os.environ['AWS_DEFAULT_REGION']

# Get the account-specific mediaconvert endpoint for this region
MC = boto3.client('mediaconvert', region_name=REGION)
ENDPOINTS = MC.describe_endpoints()
        
# Add the account-specific endpoint to the client session 
MEDIACONVERT = boto3.client('mediaconvert', region_name=REGION, endpoint_url=ENDPOINTS['Endpoints'][0]['Url'], verify=False)
        

def lambda_handler(event, context):
    #Grab Event Info + Enviornment Variables
    assetID = str(uuid.uuid4())
    jobMetadata = {'assetID': assetID}
    sourceS3Bucket = event['Records'][0]['s3']['bucket']['name']
    sourceS3Key = event['Records'][0]['s3']['object']['key']
    sourceS3 = 's3://'+ sourceS3Bucket + '/' + sourceS3Key
    sourceS3Basename = os.path.splitext(os.path.basename(sourceS3))[0]
    destinationS3 = 's3://' + os.environ['DestinationBucket']
    mediaConvertRole = os.environ['MediaConvertRole']
    
    # Loop through records provided by S3 Event trigger
    for s3_record in event['Records']:
        LOGGER.info("Working on new s3_record...")
        
        # Extract the Key and Bucket names for the asset uploaded to S3
        key = s3_record['s3']['object']['key']
        bucket = s3_record['s3']['bucket']['name']
        LOGGER.info("Bucket: {} \t Key: {}".format(bucket, key))
        

        
        # Load Job Settings Template
        LOGGER.info("Loading Job Settings...")
        with open('job_template.json') as json_data:
            jobSettings = json.load(json_data)
        jobSettings['Inputs'][0]['FileInput'] = sourceS3
     
        basekey = 'assets/' 
        S3KeyHLS = basekey + assetID +'/HLS/'+ sourceS3Basename
        S3KeyPath = basekey + assetID + '/MP4/' + sourceS3Basename
        S3KeyThumbnails = basekey + assetID + '/Thumbnails/' + sourceS3Basename

        LOGGER.info("Creating MediaConvert Job...") 
        #update job.json
        update_job_settings(jobSettings,assetID,destinationS3,S3KeyHLS,S3KeyPath,S3KeyThumbnails)
        MEDIACONVERT.create_job(Role=mediaConvertRole, UserMetadata=jobMetadata, Settings=jobSettings)

def update_job_settings(jobsettings,assetID,destinationBucket,S3HLS, S3MP4, S3Thumb):
    """
    Update MediaConvert Job Settings
    
    :param jobsettings:         Loaded JobSettings JSON template
    :param assetID:             Tagged Metadata ID
    :param destinationBucket:   Bucket for Transcoded Media to reside
    :param S3HLS                S3 path for HLS transcode files
    :param S3MP4                S3 path for Mp4 transcode files
    :param S3Thunb              S3 path for generated thumbnail files
    :return:
    """
    LOGGER.info("Updating Job Settings...")
    jobsettings['OutputGroups'][0]['OutputGroupSettings']['HlsGroupSettings']['Destination'] \
    = destinationBucket + '/' + S3HLS
    
    #S3KeyPath = 'assets/SD/' + assetID + '/MP4/' + destinationBucket
    jobsettings['OutputGroups'][1]['OutputGroupSettings']['FileGroupSettings']['Destination'] \
    = destinationBucket + '/' + S3MP4
    LOGGER.info(jobsettings['OutputGroups'][1]['OutputGroupSettings']['FileGroupSettings']['Destination'])
    
    #S3KeyThumbnails = 'assets/SD/' + assetID + '/Thumbnails/' + S3Thumb
    jobsettings['OutputGroups'][2]['OutputGroupSettings']['FileGroupSettings']['Destination'] \
    = destinationBucket + '/' + S3Thumb
    LOGGER.info(jobsettings['OutputGroups'][2]['OutputGroupSettings']['FileGroupSettings']['Destination'])
    LOGGER.info("Updated Job Settings...")
{"mode":"full","isActive":false}
