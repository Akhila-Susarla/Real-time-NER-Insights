#!/usr/bin/env python3
"""
Reads Reddit comments from Kafka topic1, extracts named entities with NLTK,
keeps a running count, and writes to topic2 every 30 s.
"""
import json, nltk
from nltk import word_tokenize, pos_tag, ne_chunk
from pyspark.sql import SparkSession, functions as F, types as T

# Download NLTK data (required for NER)
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')

BOOTSTRAP = "localhost:9092"
TOPIC_IN  = "topic1"
TOPIC_OUT = "topic2"

# ── NER helper using NLTK ────────────────────────────────────────────────
# def extract_ents(text: str):
#     """Return a list of entity strings found in `text`."""
#     tree = ne_chunk(pos_tag(word_tokenize(text)))
#     ents = []
#     for node in tree:
#         if hasattr(node, "label"):
#             token = " ".join(leaf[0] for leaf in node.leaves())
#             ents.append(token)
#     return ents

def extract_ents(text: str):
    """Return a list of entity strings found in `text`."""
    try:
        tree = ne_chunk(pos_tag(word_tokenize(text)))
        ents = []
        for node in tree:
            if hasattr(node, "label"):
                token = " ".join(leaf[0] for leaf in node.leaves())
                ents.append(token)
        print(f"Extracted entities from text '{text}': {ents}")  # Debug print
        return ents
    except Exception as e:
        print(f"Error in extract_ents for text '{text}': {e}")
        return []

ent_udf = F.udf(extract_ents, T.ArrayType(T.StringType()))

# ── Spark session ────────────────────────────────────────────────────────
spark = (
    SparkSession.builder
    .appName("NLTK-NER-Streaming")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

# ── Read from topic1 ─────────────────────────────────────────────────────
lines = (
    spark.readStream.format("kafka")
         .option("kafka.bootstrap.servers", BOOTSTRAP)
         .option("subscribe", TOPIC_IN)
         .option("startingOffsets", "earliest")
         .option("failOnDataLoss", "false")
         .load()
         .selectExpr("CAST(value AS STRING)")
)

# ── Explode entities and maintain running count ─────────────────────────
entities = lines.withColumn("entity", F.explode(ent_udf("value")))
running = entities.groupBy("entity").count()
# running = running.withColumn("count", F.col("count").cast("integer"))

running = running.withColumn("count", F.col("count").cast("integer"))

# Debug: Print the running counts
running.writeStream \
       .format("console") \
       .outputMode("complete") \
       .trigger(processingTime="30 seconds") \
       .start()

# Define result_df as the cleaned, NER-enriched DataFrame
result_df = running

# ── Write to topic2 every 30 seconds ────────────────────────────────────
# Manually construct JSON string to ensure count is a number (not a string)
out_df = result_df.select(
    F.concat(
        F.lit('{"entity":"'),
        F.col("entity"),
        F.lit('","count":'),
        F.col("count").cast("integer"),  # Ensure count is an integer
        F.lit("}")
    ).alias("value")
)

query = (
    out_df.writeStream
          .format("kafka")
          .option("kafka.bootstrap.servers", BOOTSTRAP)
          .option("topic", TOPIC_OUT)
          .option("checkpointLocation", "/tmp/spark_chk_topic2")
          .outputMode("complete")  # Changed from append to complete
          .trigger(processingTime="30 seconds")
          .start()
)

query.awaitTermination()