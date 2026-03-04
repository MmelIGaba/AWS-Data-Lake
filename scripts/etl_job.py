import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import year, month, col, to_date

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)

# Read directly from S3
df = spark.read \
    .option("header", "true") \
    .option("inferSchema", "true") \
    .csv("s3://covid19-bucket-1-mmela/raw/owid-covid-data.csv")

# Parse date column and extract year and month
df = df.withColumn("date", to_date(col("date"), "yyyy-MM-dd"))
df = df.withColumn("year", year(col("date")))
df = df.withColumn("month", month(col("date")))

# Drop rows where location or date is null
df = df.filter(col("location").isNotNull() & col("date").isNotNull())

# Write to processed path as Parquet with Snappy compression partitioned by year and month
df.write \
    .mode("overwrite") \
    .partitionBy("year", "month") \
    .option("compression", "snappy") \
    .parquet("s3://covid19-bucket-1-mmela/processed/")

job.commit()