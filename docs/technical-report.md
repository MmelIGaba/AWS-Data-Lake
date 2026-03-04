# Technical Report: Serverless Data Lake on AWS

---

## Page 1: Architecture and Design Decisions

### Overview
A fully serverless data lake was designed and implemented on AWS to ingest, catalog, transform, and analyze the Our World in Data COVID-19 dataset. The architecture follows AWS Well-Architected Framework principles with emphasis on cost optimization, security, and operational excellence.

### Dataset
- Source: Our World in Data COVID-19 dataset
- Format: CSV
- Size: 47.4 MB
- Granularity: Daily records per country
- Fields: 67 columns including cases, deaths, vaccinations, and demographic indicators

### Architecture Components

| Component | Service | Purpose |
|---|---|---|
| Storage | Amazon S3 | Raw, processed, and query result storage |
| Cataloging | AWS Glue Data Catalog | Schema registry and table management |
| ETL | AWS Glue ETL Job | CSV to Parquet transformation |
| Query | Amazon Athena | Serverless SQL analytics |
| Governance | AWS Lake Formation | Fine-grained access control |
| Automation | Lambda + EventBridge | Scheduled pipeline execution |
| Monitoring | Amazon CloudWatch | Logging and operational visibility |

### Data Lake Layers

Three logical layers were implemented:

Raw Layer: Original CSV data stored unmodified in s3://covid19-bucket-1-mmela/raw/. Serves as the source of truth and enables reprocessing.

Processed Layer: Cleaned, partitioned Parquet data stored in s3://covid19-bucket-1-mmela/processed/. Optimized for analytical queries.

Analytics Layer: Athena views and query results stored in s3://covid19-bucket-1-mmela/athena-results/. Serves as the consumption layer.

### Design Decisions

Serverless was chosen over provisioned infrastructure to eliminate operational overhead, enable pay-per-use pricing, and scale automatically with query volume.

Glue was chosen over EMR because the dataset size does not justify a persistent cluster. Glue provides managed Spark execution without cluster management.

Athena was chosen over Redshift because the query pattern is ad-hoc and infrequent. Redshift is cost-justified only for high-concurrency, sustained workloads.

---

## Page 2: ETL Strategy, Partitioning, and Performance Optimization

### ETL Pipeline

The Glue ETL job reads raw CSV directly from S3, applies transformations, and writes optimized Parquet output to the processed prefix. The job runs on 2 G.1X workers using Glue 3.0.

### Transformations Applied

| Transformation | Justification |
|---|---|
| CSV to Parquet | Columnar format enables column pruning in Athena |
| Snappy compression | Reduces storage cost and query data transfer |
| Date parsing | Ensures correct type for time-based analytics |
| Year/month extraction | Enables partition-based query optimization |
| Null filtering on location and date | Removes records with no analytical value |

### Partition Strategy

Processed data is partitioned by year and month. This strategy was selected because:

- Most analytical queries are time-based
- Partitioning by day would create excessive small files
- Partitioning by country would create high cardinality with uneven distribution
- Year and month provides balanced partition sizes with meaningful pruning benefit

Resulting structure:  
processed/  
year=2020/month=1/  
year=2020/month=2/  
year=2021/month=1/  


### Performance and Cost Evidence

The same query was executed against both raw and processed tables:

| Table | Format | Data Scanned |
|---|---|---|
| raw | CSV unpartitioned | 47.4 MB |
| processed | Parquet Snappy partitioned | 0.9 MB |

This represents a 98% reduction in data scanned per query, directly translating to a 98% reduction in Athena query cost.

### Automated Pipeline

An EventBridge rule triggers a Lambda function daily. The Lambda function starts the Glue ETL job followed by the processed data crawler. This ensures the data lake stays current without manual intervention.

---

## Page 3: Governance, IAM Model, Cost Strategy, Limitations, and Enhancements

### IAM Model

Least privilege was enforced across all service roles:

| Role | Permissions | Purpose |
|---|---|---|
| GlueDataLakeRole | S3 read/write, Glue catalog, CloudWatch | ETL job execution |
| AthenaDataLakeRole | S3 read on processed, write on athena-results | Query execution |
| LambdaGlueTriggerRole | Glue StartJobRun, StartCrawler | Pipeline automation |
| EventBridgeGlueRole | Lambda InvokeFunction | Schedule trigger |

### Lake Formation Governance

Lake Formation was implemented as a second layer of access control beyond IAM. This separation ensures that even if IAM policies are misconfigured, Lake Formation enforces data-level permissions independently.

Permissions granted:

- AthenaDataLakeRole: SELECT and DESCRIBE on all tables in datalake_db
- GlueDataLakeRole: CREATE_TABLE, DESCRIBE, ALTER, INSERT on datalake_db
- DATA_LOCATION_ACCESS granted on both raw and processed S3 paths

### Cost Strategy

| Strategy | Implementation | Impact |
|---|---|---|
| Parquet conversion | Glue ETL job | 98% scan reduction |
| Snappy compression | Glue ETL job | Reduced storage and transfer |
| Partition pruning | Year/month partitions | Targeted scans only |
| Workgroup scan limit | 1GB per query cap | Prevents cost overruns |
| S3 lifecycle policy | Glacier transition after 30 days | Reduces raw storage cost |

At scale, 1,000,000 queries per month against the processed table costs \$4.50 compared to \$237.00 against the raw table.

### Known Limitations

- Year and month partition columns stored as string type requiring quoted values in WHERE clauses
- No incremental load strategy implemented. Full rewrite on every ETL run
- No data quality validation beyond null filtering on two columns
- Row-level security not implemented in this iteration
- Lambda function has no error handling for concurrent Glue job runs

### Enhancements

- Cast year and month to integer during ETL to simplify query syntax
- Implement Glue job bookmarks for incremental processing
- Add AWS Glue Data Quality rules for schema validation
- Implement Lake Formation row-level security using data cell filters
- Add CloudWatch Alarms with SNS notifications for pipeline failure alerting
- Apply AWS cost allocation tags to all resources for granular billing visibility
- Extend pipeline to support additional datasets using the same architecture pattern
EOF
- Implement Amazon QuickSight dashboard connected to Athena for self-service BI, 
- visualizing monthly case trends, vaccination progress by continent, and death rate by country