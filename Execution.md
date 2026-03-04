## Phase 1 – Secure S3 Data Lake Foundation

### Overview

Phase 1 focuses on establishing a secure, production-ready Amazon S3 bucket to serve as the foundational storage layer for the data lake architecture.

This phase implements:

- Secure bucket creation (us-east-1)
- Versioning
- Default encryption
- Public access blocking
- IAM-only access model
- Structured folder layout
- Lifecycle cost optimization

---

### 1. Bucket Creation

**Region:** us-east-1  
**Bucket Type:** Private, versioned, encrypted  

#### Key Configuration Decisions

| Setting | Value |
|----------|--------|
| Region | us-east-1 |
| Versioning | Enabled |
| Default Encryption | SSE-S3 (AES256) |
| Public Access | Fully Blocked |
| Access Control Model | IAM-only |

#### Rationale

- **us-east-1** selected as default region for consistency.
- Versioning protects against accidental deletion or overwrites.
- SSE-S3 enforces encryption at rest.
- Public access is completely disabled to prevent data exposure.
- IAM-only access ensures centralized identity-based security control.

---

### 2. Folder Structure (Logical Data Lake Layout)

Although S3 does not support real directories, logical prefixes were created to simulate structured storage.
```
raw/
processed/
athena-results/
```

### Purpose of Each Layer

| Prefix | Purpose |
|--------|----------|
| raw/ | Immutable ingestion layer (source data) |
| processed/ | Transformed and cleaned datasets |
| athena-results/ | Query results output location |

### Architecture Model
Data Source  
↓  
raw/  
↓  
processed/  
↓  
Athena Queries → athena-results/


This follows standard data lake layering principles.

---

## 3. Lifecycle Policy (Cost Optimization)

A lifecycle rule was configured for long-term cost control.

### Rule Configuration

| Prefix | Action | After | Storage Class |
|--------|--------|--------|---------------|
| raw/ | Transition | 30 days | GLACIER |

### Rationale

Raw ingestion data is infrequently accessed after processing.  
Automatically transitioning to Glacier reduces storage costs while preserving archival capability.

This supports scalable and cost-efficient data lake growth.

---

## 4. Encryption Configuration

Default server-side encryption is enabled using:  
SSE-S3 (AES256)

### Why SSE-S3?

- Automatically encrypts all objects at rest
- No key management overhead
- Meets baseline security best practices
- Suitable for analytics workloads

---

## 5. Public Access Protection

S3 Block Public Access was enabled with the following settings:

| Setting | Value |
|-----------|--------|
| BlockPublicAcls | true |
| IgnorePublicAcls | true |
| BlockPublicPolicy | true |
| RestrictPublicBuckets | true |

### Security Impact

- Prevents accidental public exposure
- Overrides any future public ACL or policy
- Enforces private-by-default storage

---

## 6. IAM-Only Access Model

Validation confirmed:

- No bucket policy exists (`NoSuchBucketPolicy`)
- No public ACL grants
- Access is controlled strictly via IAM users and roles

### Access Flow
IAM User / Role  
↓  
IAM Policy  
↓  
S3 Bucket

No IAM permission = no access.

This enforces centralized identity and access management.

---

## 7. Security Posture Summary

| Control | Status |
|----------|--------|
| Encryption at Rest | Enabled |
| Versioning | Enabled |
| Public Access | Fully Blocked |
| IAM Enforcement | Active |
| Lifecycle Management | Configured |
| Data Segmentation | Structured |

---

## 8. Phase 1 Outcome

Phase 1 establishes a secure, scalable, and cost-optimized S3 foundation suitable for:

- Analytics workloads
- Athena querying
- Glue catalog integration
- ETL pipelines
- Portfolio demonstration of AWS proficiency

The storage layer is now production-aligned and ready for:

- Phase 2: Glue Data Catalog configuration
- Phase 3: Athena integration
- Phase 4: ETL / transformation pipelines

---

**Phase 1 Status:** Complete  
**Security Level:** Production-Ready  
**Architecture Level:** Solutions Architect Associate Standard

---
---
## Phase 2 – Governance, Metadata & Service Role Configuration

### Overview

Phase 2 focuses on establishing the compute, metadata, and governance control layers for the data lake architecture.

This phase implements:

- IAM role for AWS Glue (ETL layer)
- IAM role for Athena (query layer)
- IAM role for Lake Formation (governance layer)
- Strict least-privilege access model
- Service-level responsibility separation
- Glue Data Catalog readiness

---

## 1. Glue Service Role (ETL Layer)

**Role Name:** `GlueDataLakeRole`  
**Purpose:** Execute crawlers and ETL jobs securely.

### Permissions Model

| Resource | Access Level |
|----------|--------------|
| raw/ | Read-only |
| processed/ | Write |
| Glue Data Catalog | Full access (required for ETL operations) |

### Design Rationale

- Glue reads immutable ingestion data from `raw/`
- Writes transformed datasets to `processed/`
- Updates Glue Data Catalog metadata
- Follows least-privilege principle while enabling ETL workflows

---

## 2. Athena Service Role (Query Layer)

**Role Name:** `AthenaDataLakeRole`  
**Purpose:** Execute queries on processed datasets and store results.

### Permissions Model

| Resource | Access Level |
|----------|--------------|
| processed/ | Read-only |
| athena-results/ | Write |

### Design Rationale

- Athena cannot modify raw or processed data
- Query results stored separately in `athena-results/`
- Enforces separation of compute and storage responsibilities

---

## 3. Lake Formation Admin Role (Governance Layer)

**Role Name:** `LakeFormationAdminRole`  
**Purpose:** Manage data lake governance, catalog permissions, and metadata security.

### Permissions Model

| Service | Access Level |
|---------|--------------|
| Lake Formation | Full (`lakeformation:*`) |
| Glue Catalog | Catalog-level management (create, update, delete tables & databases) |

### Design Rationale

- Governance-only role; no S3 or Athena permissions
- Wildcard permissions only where required by AWS governance model
- Strictly scoped to metadata management and policy enforcement

---

## 4. Service Role Separation

| Layer | Service | Role |
|-------|---------|------|
| ETL / Transformation | AWS Glue | GlueDataLakeRole |
| Query / Analytics | Athena | AthenaDataLakeRole |
| Governance / Catalog | Lake Formation | LakeFormationAdminRole |

### Benefits

- Clear separation of responsibilities
- Least-privilege enforcement
- Enterprise-grade governance and access control
- Reduces risk of accidental data exposure or modification

---

## 5. Phase 2 Outcome

Phase 2 establishes:

- Proper IAM roles for Glue, Athena, and Lake Formation
- Least-privilege access across S3 and catalog
- Foundation for Glue Database, Crawler, and Athena query workflows
- Governance-ready data lake architecture

**Phase 2 Status:** Complete  
**Security Level:** Production-Ready  
**Architecture Level:** Solutions Architect Associate Standard

---
---

## Phase 3 – Data Cataloging with Glue

### Goal
Register and classify raw data in the Glue Data Catalog.

### Actions Performed

1. **Create Glue Database**
   - Name: `datalake_db`

2. **Configure Glue Crawler**
   - **Target:** `raw/` S3 path
   - **Assign IAM Role:** `GlueDataLakeRole`
   - **Output:** `datalake_db` Glue database
   - **Enable Partition Detection:** Yes (no partitions expected for this dataset)

3. **Run Crawler**
   - Initial runs encountered **S3 path not found** and **access denied (403) errors** due to IAM permissions.
   - Permissions were corrected; crawler successfully ran to completion.

### Validation Results

#### Schema Correctness
- Table `raw` was created in `datalake_db`.
- Columns detected:

| Column Name           | Inferred Type |
|-----------------------|---------------|
| iso_code              | string        |
| continent             | string        |
| location              | string        |
| date                  | string        |
| total_cases           | double        |
| new_cases             | double        |
| new_cases_smoothed    | double        |
| total_deaths          | double        |
| new_deaths            | double        |
| new_deaths_smoothed   | double        |

#### Data Types Accuracy
- Detected types match expectations:
  - `string` → iso_code, continent, location, date  
  - `double` → total_cases, new_cases, new_cases_smoothed, total_deaths, new_deaths, new_deaths_smoothed

#### Partitions Detected
- No partitions were expected; table is correctly unpartitioned.

### Outcome
- Raw data is now registered and classified in Glue.
- Table schema is correct, data types are accurate, and the catalog is ready for downstream ETL and Athena queries.

---
---

### PHASE 4 DOCUMENTATION — LAKE FORMATION GOVERNANCE

#### OBJECTIVE

Implement data governance using AWS Lake Formation to enforce fine-grained access control over the data lake, beyond what IAM alone provides.

#### ARCHITECTURE DECISION

IAM controls service-level access. Lake Formation controls data-level access. Both are required. IAM determines what services a role can call. Lake Formation determines what data those services can see. This separation is a core principle of the AWS data governance model.

##### STEPS EXECUTED

Step 1: Register S3 Bucket

Registered the data lake S3 bucket with Lake Formation. This transfers ownership of data access decisions from IAM to Lake Formation for all registered paths.

Step 2: Assign Data Lake Administrator

Assigned the IAM user as the Lake Formation administrator. This grants full governance control over all registered resources and databases.

Step 3: Grant Database-Level Permission

Granted DESCRIBE permission on datalake_db to the Athena role. This allows the role to see the database and its contents in the Glue catalog.

Step 4: Grant Table-Level Permission

Granted SELECT and DESCRIBE on all current and future tables in datalake_db to the Athena role. TableWildcard ensures new tables created after this grant are automatically covered.

Step 5: Validate Permissions

Listed all permissions granted to the Athena role to confirm configuration is correct.

#### ACCESS CONTROL MODEL

##### AthenaDataLakeRole:

Can query all tables in datalake_db
Cannot modify or delete data
Cannot access tables outside datalake_db
Cannot administer Lake Formation
Data Lake Administrator:

##### Full governance control
Can grant and revoke permissions
Can register and deregister resources
KNOWN LIMITATIONS AND ENHANCEMENTS

##### Limitations:

Row-level filtering not implemented in this iteration
Column-level restrictions not applied to sensitive columns
Single database scope
Enhancements:

Implement Lake Formation data filters for row-level security
Apply column-level restrictions on demographic fields such as population and gdp_per_capita
Extend governance to cover future databases as the lake grows

---

### PHASE 5 DOCUMENTATION — SERVERLESS ETL TRANSFORMATION

Objective
Transform raw CSV data into an optimized, analytics-ready format using AWS Glue, reducing Athena query cost and improving performance.

Architecture Decision
Raw CSV data is inefficient for analytical queries. It requires full file scans, has no compression, and has no partitioning. Converting to Parquet with Snappy compression and partitioning by year and month directly addresses these inefficiencies. This is a core cost optimization pattern in data lake architecture.

What Was Done
Glue ETL Job

Created a Glue ETL job using GlueDataLakeRole with the following transformations:

- Read raw CSV directly from S3
- Parsed date column into proper date type
- Derived year and month columns from date
- Dropped rows where location or date was null
- Wrote output to processed/ as Parquet with Snappy compression
- Partitioned output by year and month

Processed Data Structure

```
s3://covid19-bucket-1-mmela/processed/
  year=2020/
    month=1/
    month=2/
  year=2021/
    month=1/
```

### Processed Layer Implementation

#### Processed Crawler

A second AWS Glue crawler was created and executed targeting the `processed/` S3 prefix.

**Outcome:**

- Registered a new table in `datalake_db`
- Correct schema inferred automatically
- Data types properly detected
- Partition keys automatically identified (`year`, `month`)
- Table ready for Athena querying

This ensures the processed layer is fully cataloged and governed independently from the raw layer.

---

#### Transformations Applied

| Transformation | Reason |
|---------------|--------|
| **CSV → Parquet** | Columnar format significantly reduces Athena scan size and improves query performance |
| **Snappy Compression** | Reduces storage costs and improves read throughput |
| **Partition by `year` / `month`** | Enables partition pruning, minimizing scanned data during queries |
| **Date Parsing** | Ensures proper `DATE` or `TIMESTAMP` data types for accurate time-based analytics |
| **Null Filtering (`location`, `date`)** | Removes analytically invalid records, improving data quality |

---

#### Architectural Significance

The processed layer represents the **analytics-ready zone** of the data lake:

- Optimized for performance
- Structured for query efficiency
- Partition-aware
- Cleaned and quality-controlled
- Governed via Lake Formation

Raw data remains immutable and restricted, while processed data becomes the controlled consumption layer for Athena and downstream analytics.  

### Result
Two tables now exist in datalake_db:

- raw: original CSV, unpartitioned
- processed: Parquet, Snappy compressed, partitioned by year and month

#### IAM and Lake Formation Fixes Applied
##### GlueDataLakeRole required the following to execute successfully:

- AmazonS3FullAccess for S3 read and write
- AWSGlueServiceRole for Glue catalog access
- Lake Formation DATA_LOCATION_ACCESS on the processed/ path
- Lake Formation CREATE_TABLE and DESCRIBE on datalake_db
- Lake Formation SELECT, DESCRIBE, ALTER, INSERT on all tables
### Known Limitations and Enhancements

#### Limitations

- inferSchema on CSV may miscast some sparse numeric columns
- No data quality checks beyond null filtering on two columns

#### Enhancements

- Add Great Expectations or Glue Data Quality for schema validation
- Implement incremental loads using Glue job bookmarks
Add data quality metrics to CloudWatch

---

### PHASE 6 — ATHENA QUERY LAYER

#### Objective

Implement the analytics layer using Amazon Athena to query processed data, demonstrate partition pruning, and produce measurable cost optimization evidence.

---

#### Architecture Decision

Athena was selected as the query layer because it is:

- Fully serverless (no infrastructure management)
- Natively integrated with the Glue Data Catalog
- Directly integrated with Lake Formation governance
- Priced per TB scanned

This pricing model makes performance optimization (partitioning, Parquet format, compression) directly measurable and financially meaningful.

---

#### Workgroup Configuration

A dedicated Athena workgroup was created with the following controls:

- Output location enforced to `athena-results/`
- Query result encryption enabled
- Data scan limit set to **1GB per query** to prevent runaway costs
- Centralized query monitoring and cost governance

This ensures analytics usage remains controlled and auditable.

---

#### Queries Executed

| Query | Description |
|--------|------------|
| Query 1 | Total cases by country |
| Query 2 | Monthly global new cases trend |
| Query 3 | Death rate by country |
| Query 4 | Partition-pruned query filtered by `year` and `month` |
| Query 5 | Vaccination progress by continent |
| View | `monthly_summary` reusable aggregation view |

All results were:
- Stored locally for validation
- Automatically written to `athena-results/` in S3
- Governed via Lake Formation permissions

---

#### Cost Optimization Evidence

To quantify optimization impact, the same analytical query was executed against both the raw and processed tables.

| Table | Data Scanned | Format |
|--------|--------------|--------|
| raw | 47.4 MB | CSV (unpartitioned) |
| processed | 0.9 MB | Parquet (Snappy, partitioned) |

##### Result

**98% reduction in data scanned per query**

##### Athena Pricing Impact

Athena pricing: **$5.00 per TB scanned**

- Raw query cost: **$0.000237 per query**
- Processed query cost: **$0.0000045 per query**

While these per-query costs are small, at scale (thousands or millions of queries), the cost difference becomes operationally significant.

This validates the architectural decisions made in earlier phases:
- Columnar format (Parquet)
- Snappy compression
- Strategic partitioning
- Data cleaning before analytics

---

#### Partition Pruning

Query 4 filtered using partition keys:

```sql
WHERE year = '2024'
  AND month = '01'
```
Because year and month are partition keys:

- Athena scanned only relevant partition folders

- Full dataset scan was avoided

- Query performance improved

- Data scanned was minimized

Partition pruning is only possible because:

- Partition strategy was defined in Phase 0

- Implemented during ETL

- Registered correctly via Glue crawler

This demonstrates intentional architectural planning rather than accidental optimization.

#### Known Limitations

- `year` and `month` partition columns are stored as `STRING`
- Quoted values are required in `WHERE` clauses (e.g., `year = '2024'`)
- Athena query result reuse (result caching) is not configured
- No automated query performance monitoring implemented

---

#### Enhancements

- Cast `year` and `month` to `INT` during ETL to simplify SQL syntax
- Enable Athena query result reuse to reduce repeated scan costs
- Implement Named Queries for standardized reporting and reusability
- Integrate CloudWatch metrics for query monitoring and observability
- Implement cost alerting on workgroup scan thresholds to prevent budget overruns

---

#### Final Outcome of Phase 6

The analytics layer is now:

- Serverless  
- Governed by Lake Formation  
- Cost-optimized  
- Partition-aware  
- Measurably efficient  

---

#### Architectural Capabilities Achieved

The data lake architecture now supports:

- Secure ingestion (raw layer)
- Optimized transformation (processed Parquet layer)
- Governed analytics (Athena + Lake Formation)
- Measurable cost efficiency at query scale

This completes the implementation of a controlled, optimized, and production-aligned analytics layer.


---


### PHASE 7 — MONITORING AND LOGGING

#### Objective

Verify operational visibility across Glue ETL jobs and crawlers using Amazon CloudWatch, and document the monitoring approach for production readiness.

---

#### Architecture Decision

CloudWatch is the native monitoring and observability layer for all AWS Glue operations.

All Glue job runs, crawler executions, driver logs, executor logs, and error outputs are automatically streamed to CloudWatch log groups.

No additional configuration is required beyond ensuring the Glue IAM role includes CloudWatch write permissions. This is included by default in the `AWSGlueServiceRole` managed policy.

This ensures:

- Centralized log aggregation  
- Real-time failure visibility  
- Operational traceability  
- Production-grade monitoring foundation  

---

#### Log Groups Verified

| Log Group | Purpose |
|------------|----------|
| `/aws-glue/jobs/output` | Standard output from ETL job runs |
| `/aws-glue/jobs/error` | Error output from failed ETL job runs |
| `/aws-glue/jobs/logs-v2` | Detailed Spark driver and executor logs |
| `/aws-glue/crawlers` | Crawler execution logs |

All expected log groups were verified as present and actively receiving logs.

---

#### Logs Captured

| File | Contents |
|-------|----------|
| `glue_job_logs.json` | Output logs from successful ETL job run |
| `crawler_logs.json` | Logs from `covid19-processed-crawler` execution |

Logs were exported for documentation and validation purposes.

---

#### Failure Detection

During implementation, CloudWatch logs were used to identify and resolve the following issues:

- `GlueETLRole` trust policy missing Glue service principal  
- `GlueDataLakeRole` missing S3 read permissions  
- `GlueDataLakeRole` missing Glue catalog permissions  
- Lake Formation blocking crawler access to processed path  

Each failure generated a precise error message in CloudWatch, clearly identifying the permission or configuration gap.

This validated that monitoring was functioning correctly and provided actionable diagnostic information.

---

#### Monitoring Approach (Production Model)

In a production environment, the following controls would be implemented:

- CloudWatch Alarms on Glue job failure state  
- SNS notifications triggered by alarm state changes  
- CloudWatch Dashboard aggregating:
  - Job duration  
  - DPU usage  
  - Success vs failure rate  
- Log retention policy set to 30 days to manage storage costs  

This approach ensures proactive operational monitoring rather than reactive troubleshooting.

---

#### Known Limitations

- No CloudWatch alarms configured in this implementation  
- No CloudWatch dashboard created  
- Log retention policy not explicitly configured  

---

#### Enhancements

- Implement CloudWatch Alarm for Glue job failure notification via SNS  
- Create a CloudWatch Dashboard for operational visibility  
- Set log retention to 30 days across all Glue log groups  

---

#### Final Outcome of Phase 7

The data lake now includes:

- Verified operational logging  
- Structured failure diagnostics  
- Clear audit trail for ETL and crawler activity  
- Production-aligned monitoring design  

This completes the observability layer of the serverless data lake architecture, ensuring it is not only functional and optimized, but also operationally visible and maintainable.

---

### PHASE 8 — AUTOMATEventBridge (daily rate)
│  
▼  
Lambda: covid19-glue-trigger  
│  
├── Start Glue ETL Job: covid19-etl-job  
│  
└── Start Glue Crawler: covid19-processed-crawlerED INGESTION PIPELINE

#### Objective

ImplemEventBridge (daily rate)
│  
▼  
Lambda: covid19-glue-trigger  
│  
├── Start Glue ETL Job: covid19-etl-job  
│  
└── Start Glue Crawler: covid19-processed-crawlerent automated pipeline orchestration using Amazon EventBridge and AWS Lambda to trigger the Glue ETL job and crawler on a daily schedule, eliminating manual intervention.

---

#### Architecture DeciEventBridge (daily rate)
│  
▼  
Lambda: covid19-glue-trigger  
│  
├── Start Glue ETL Job: covid19-etl-job  
│  
└── Start Glue Crawler: covid19-processed-crawlersion  

EventBridge cannot directly invoke Glue jobs or crawlers.  
A Lambda function is used as an intermediary, following the recommended AWS design pattern.  

Benefits of this approach:

- Centralized trigger point for ETL and crawler
- Can include notifications, logging, or conditional logic
- Fully serverless orchestration
- Extensible for future automation requirements

---

#### Components ImplemEventBridge (daily rate)
│  
▼  
Lambda: covid19-glue-trigger  
│  
├── Start Glue ETL Job: covid19-etl-job  
│  
└── Start Glue Crawler: covid19-processed-crawlerented  

| Component | Purpose |
|-----------|--------|
| **EventBridge Rule** | Schedules trigger on a daily rate |
| **Lambda Function** | Intermediary that starts Glue ETL job and crawler |
| **LambdaGlueTriggerRole** | IAM role allowing Lambda to invoke Glue |
| **EventBridgeGlueRole** | IAM role allowing EventBridge to invoke Lambda |

---

#### Automation Flow
EventBridge (daily rate)  
│  
▼  
Lambda: covid19-glue-trigger  
│  
├── Start Glue ETL Job: covid19-etl-job  
│  
└── Start Glue Crawler: covid19-processed-crawler  


**Execution Order:**

1. Lambda starts the ETL job first to process any new raw data  
2. Upon ETL completion, Lambda triggers the crawler to update the Glue catalog with schema and partition changes  

This ensures data freshness and catalog consistency.

---

#### Configuration Details

- EventBridge rule configured with a daily rate schedule  
- Lambda function uses **Boto3** (Python SDK) to start Glue ETL job and crawler  
- IAM roles provide least-privilege access for Lambda and EventBridge  

This provides a fully automated ingestion pipeline without manual intervention.

---

#### Known Limitations

- No error handling in Lambda if Glue job is already running  
- No SNS notification on pipeline failure  
- Pipeline runs daily regardless of whether new data exists in `raw/`  

---

#### Enhancements

- Add S3 event trigger to invoke Lambda only when new data lands in `raw/`  
- Add error handling and retry logic within Lambda  
- Implement SNS alerts on Glue job or crawler failure  
- Use Step Functions for complex orchestration with conditional branching and parallelism  

---

#### Final Outcome of Phase 8

The automated ingestion pipeline now:

- Runs without manual intervention  
- Processes raw data daily and updates the processed catalog  
- Provides a foundation for alerting and conditional logic in future iterations  
- Completes the automation layer of the enterprise-grade data lake architecture  

,
===

### PHASE 9 — COST OPTIMIZATION ANALYSIS

#### Objective

Demonstrate cost awareness and optimization strategies applied throughout the data lake architecture, with measurable evidence.

---

#### Cost Optimization Strategies Applied

1. **Parquet Conversion**  
   - Raw data initially stored as CSV requires full file scans on every query.  
   - Converting to Parquet enables **column pruning**, so Athena reads only referenced columns, reducing scan volume.

2. **Snappy Compression**  
   - Applied to all Parquet output files.  
   - Reduces S3 storage costs and volume of data transferred during Athena queries.

3. **Partitioning by Year and Month**  
   - Processed data is partitioned by `year` and `month`.  
   - Athena uses Glue catalog metadata to **skip irrelevant partitions**.  
   - Queries filtered by year/month scan only the relevant folders, improving performance and lowering cost.

4. **Athena Workgroup Scan Limit**  
   - Set a **1GB per query** scan limit on the `covid19-workgroup`.  
   - Prevents runaway queries from incurring unexpected costs.

5. **S3 Lifecycle Policy**  
   - Configured on `raw/` prefix to transition data to Glacier after 30 days.  
   - Raw data is retained for reprocessing but does not occupy S3 Standard storage unnecessarily.

---

#### Measured Cost Evidence

| Table | Format | Data Scanned | Athena Cost per Query |
|-------|--------|--------------|---------------------|
| raw | CSV unpartitioned | 47.4 MB | $0.000237 |
| processed | Parquet Snappy partitioned | 0.9 MB | $0.0000045 |

**Result:** 98% reduction in data scanned per query, demonstrating measurable cost efficiency.

---

#### Projected Cost at Scale

**10,000 queries per month:**

| Table | Monthly Athena Cost |
|-------|------------------|
| raw | $2.37 |
| processed | $0.045 |

**1,000,000 queries per month:**

| Table | Monthly Athena Cost |
|-------|------------------|
| raw | $237.00 |
| processed | $4.50 |

At scale, the cost difference validates the ETL transformation and partitioning strategy.

---

#### AWS Free Tier Considerations

| Service | Free Tier Limit | Usage |
|---------|----------------|-------|
| S3 | 5GB storage, 20,000 GET requests | Within limit |
| Glue | 1,000,000 objects cataloged free | Within limit |
| Athena | First 1TB scanned per month free | Well within limit |
| Lambda | 1,000,000 requests per month free | Within limit |
| CloudWatch | 5GB log ingestion free | Within limit |

All components were successfully implemented within AWS Free Tier constraints for this project.

---

#### Known Limitations

- Cost projections are based on a single dataset size; real-world queries may vary  
- No AWS cost allocation tags applied to resources, limiting granular billing visibility  

---

#### Enhancements

- Apply AWS cost allocation tags to all resources for detailed billing  
- Enable S3 Intelligent Tiering for automatic storage class optimization  
- Use Athena query result reuse to eliminate redundant scans on repeated queries  

---

#### Final Outcome of Phase 9

The data lake architecture now demonstrates:

- **Optimized storage formats** (Parquet + Snappy)  
- **Partition-aware processing**  
- **Controlled query execution** via Athena workgroup limits  
- **Measured cost reductions** of up to 98% per query  
- **Free Tier-compliant implementation**  

These measures validate both performance and financial efficiency, supporting production-grade data lake operations.

