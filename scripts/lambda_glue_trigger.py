import boto3

def lambda_handler(event, context):
    glue = boto3.client('glue')
    
    # Start ETL job
    job_response = glue.start_job_run(JobName='covid19-etl-job')
    
    # Start processed crawler
    crawler_response = glue.start_crawler(Name='covid19-processed-crawler')
    
    return {
        'JobRunId': job_response['JobRunId'],
        'CrawlerStatus': 'Started'
    }
