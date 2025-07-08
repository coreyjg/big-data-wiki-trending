#!/usr/bin/env python3
"""
spark_stream.py

Real-time Wikipedia Trending Stream Processor.

This script reads Wikipedia edit events from a Kafka topic using
Spark Structured Streaming, computes sliding-window counts of edit
activity per page title, and writes the aggregated results to Cassandra.

Configuration can be overridden via environment variables:
  KAFKA_BOOTSTRAP_SERVERS (default: localhost:9092)
  KAFKA_TOPIC            (default: wiki.pageviews)
  CASSANDRA_HOST         (default: 127.0.0.1)
  CASSANDRA_USER         (default: cassandra)
  CASSANDRA_PASS         (default: cassandra)
  CHECKPOINT_LOCATION    (default: /tmp/wiki_cassandra_ckpt)

Usage:
  # via env vars
  export KAFKA_BOOTSTRAP_SERVERS="kafka:9092"
  export CASSANDRA_HOST="cass1.local"
  spark-submit spark_stream.py

  # or with argparse flags
  spark-submit spark_stream.py \
    --kafka-bootstrap kafka:9092 \
    --cass-host cass1.local \
    --checkpoint /mnt/data/ckpt
"""
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, window
from pyspark.sql.types import *


# --- CONFIGURATION (env-vars with defaults) ---
# Loads Kafka, Cassandra, and checkpoint settings from environment variables, falling back to sensible defaults.
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC      = os.getenv("KAFKA_TOPIC", "wiki.pageviews")
CASS_HOST        = os.getenv("CASSANDRA_HOST", "127.0.0.1")
CASS_USER        = os.getenv("CASSANDRA_USER", "cassandra")
CASS_PASS        = os.getenv("CASSANDRA_PASS", "cassandra")
CKPT_LOCATION    = os.getenv("CHECKPOINT_LOCATION", "/tmp/wiki_cassandra_ckpt")


# --- Spark Session Initialization ---
# Builds or retrieves a SparkSession named "WikiTrending".
# Configures connectivity to Cassandra for storing results.
# Added Cassandra connection settings
spark = SparkSession.builder \
    .master("local[*]") \
    .appName("WikiTrending") \
    .config("spark.cassandra.connection.host", CASS_HOST) \
    .config("spark.cassandra.auth.username", CASS_USER) \
    .config("spark.cassandra.auth.password", CASS_PASS) \
    .getOrCreate()

# --- LOGGING CONFIGURATION ---
# Sets Spark’s log level to WARN to reduce console noise from INFO and DEBUG messages.
spark.sparkContext.setLogLevel("WARN")

# --- JSON Schema Definition ---
# Defines the expected payload structure for recent change events.
schema = StructType([
    StructField("$schema", StringType()),
    StructField("meta", MapType(StringType(), StringType())),
    StructField("id", StringType()),
    StructField("namespace", IntegerType()),
    StructField("title", StringType()),
    StructField("wiki", StringType()),
    StructField("timestamp", LongType()),
])

# --- Read from Kafka Stream ---
# Creates a DataFrame representing the continuous stream of raw Kafka messages.
df_raw = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP) \
    .option("subscribe", KAFKA_TOPIC) \
    .option("startingOffsets", "earliest") \
    .load()

# --- Parse and Filter Events ---
# Extracts JSON payload, filters for English Wikipedia edits, and adds event timestamp.
df_parsed = df_raw.select(
    from_json(col("value").cast("string"), schema).alias("data")
).select("data.*")

# Filter for English Wikipedia only
df_en = df_parsed.filter(col("wiki") == "enwiki")

# Convert Unix timestamp (seconds) to Spark timestamp column
df_ts = df_en.withColumn(
    "event_time", 
    (col("timestamp") * 1000).cast("timestamp")
)

# --- Windowed Aggregation ---
# Computes counts of edits per title in 1-minute windows sliding every 30 seconds.
df_counts = df_ts.withWatermark("event_time", "2 minutes") \
    .groupBy(
        window(col("event_time"), "1 minute", "30 seconds"),
        col("title")
    ).count() \
    .selectExpr(
        "window.start as window_start",
        "window.end as window_end",
        "title",
        "count as cnt"
    )

# --- Cassandra Sink Definition ---
# Defines a function to write each micro-batch of aggregated counts to Cassandra.
def write_to_cassandra(batch_df, batch_id):
    batch_df.write \
        .format("org.apache.spark.sql.cassandra") \
        .options(keyspace="wiki", table="counts") \
        .mode("append") \
        .save()

# --- Start Streaming Query ---
# Hooks up the foreachBatch sink and starts the continuous query.
query = df_counts.writeStream \
    .foreachBatch(write_to_cassandra) \
    .outputMode("append") \
    .option("checkpointLocation", CKPT_LOCATION) \
    .start()

# --- Graceful shutdown handling ---
# Registers signal handlers so that on SIGTERM or SIGINT we stop the
# streaming query cleanly (avoiding half-written micro-batches).
import signal
import sys

def _graceful_shutdown(signum, frame):
    query.stop()
    sys.exit(0)

signal.signal(signal.SIGTERM, _graceful_shutdown)
signal.signal(signal.SIGINT, _graceful_shutdown)

# Await termination of the streaming query
query.awaitTermination()
