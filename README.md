# Serverless Data Lake on AWS

## Overview
A fully serverless data lake architecture built on AWS using S3, Glue, Athena, Lake Formation, Lambda, and EventBridge. Dataset: Our World in Data COVID-19 dataset.

## Architecture
- Storage: Amazon S3 (raw, processed, athena-results)
- Cataloging: AWS Glue Data Catalog
- ETL: AWS Glue ETL Job
- Query: Amazon Athena
- Governance: AWS Lake Formation
- Automation: AWS Lambda + Amazon EventBridge
- Monitoring: Amazon CloudWatch

## Repository Structure
- scripts/ - Glue ETL job and Lambda function
- queries/ - Athena SQL queries and views
- results/ - Query results and CloudWatch logs

## Partition Strategy
Processed data partitioned by year and month in Parquet format with Snappy compression. Achieves 98% reduction in Athena data scanned compared to raw CSV.

## Cost Optimization
- CSV to Parquet conversion
- Snappy compression
- Partition pruning
- Athena workgroup scan limit: 1GB per query
- S3 lifecycle policy on raw data

## Phases
1. S3 Data Lake Foundation
2. IAM and Access Control
3. Glue Data Cataloging
4. Lake Formation Governance
5. Serverless ETL Transformation
6. Athena Query Layer
7. Monitoring and Logging
8. Automated Pipeline via EventBridge and Lambda
