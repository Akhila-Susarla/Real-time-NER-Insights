# Real-time Named Entity Recognition (NER) Pipeline

This project implements a real-time data processing pipeline that:
1. Streams live Reddit comments from r/news
2. Processes them with Named Entity Recognition (NER)
3. Aggregates entity counts
4. Visualizes the results

## Project Structure

```
.
├── 1_producer/                   # Reddit data producer
│   └── reddit_producer.py        # Streams Reddit comments to Kafka
├── 2_spark/                      # Stream processing with Spark
│   └── ner_stream.py             # NER extraction and entity counting
├── 3_logstash/                   # Data ingestion to Elasticsearch
│   └── pipeline.conf             # Logstash configuration
├── Output Screenshots/           # Visualization screenshots
│   ├── Terminal_running_*.png    # Terminal screenshots showing execution
│   ├── Donutplot_*.png           # Donut chart visualizations (15/30/45/60 min)
│   └── Barplot_*.png             # Bar chart visualizations (15/30/45/60 min)
├── requirements.txt              # Python dependencies
└── Q1 Report.docx                # Project report with findings
```

## Technologies Used

- **Kafka**: Message broker for streaming data
- **PySpark**: Distributed processing of streaming data
- **NLTK**: Natural Language Toolkit for Named Entity Recognition
- **Logstash**: Data ingestion to Elasticsearch
- **Elasticsearch**: Storage and indexing of processed data
- **Kibana**: Visualization (for Donut and Bar plots)

## Prerequisites

- Python 3.x
- Apache Kafka
- Apache Spark
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Reddit API credentials

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up Reddit API credentials:
   ```
   export REDDIT_CLIENT_ID=your_client_id
   export REDDIT_CLIENT_SECRET=your_client_secret
   ```

3. Make sure Kafka is running:
   ```
   # Create required topics
   kafka-topics --create --bootstrap-server localhost:9092 --topic topic1
   kafka-topics --create --bootstrap-server localhost:9092 --topic topic2
   ```

4. Ensure Elasticsearch is running with the credentials specified in the Logstash configuration

## Running the Pipeline

Tab 1. Start Kafka:
   ```
   cd kafka_2.13-4.0.0
   rm -rf /tmp/kafka-logs /tmp/kraft-combined-logs 
   KAFKA_CLUSTER_ID="$(bin/kafka-storage.sh random-uuid)"
   bin/kafka-storage.sh format --standalone -t $KAFKA_CLUSTER_ID -c config/server.properties
   bin/kafka-server-start.sh config/server.properties
   ```

Tab 2. Start streaming script:
   ```
   (Activate venv)
   cd 1_producer
   export REDDIT_CLIENT_ID=your_client_id
   export REDDIT_CLIENT_SECRET=your_client_secret
   python3 reddit_producer.py
   ```

Tab 3. Start the Spark streaming job:
   ```
   (Activate venv)
   cd spark-3.5.5-bin-hadoop3
   spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.5 \
  ~/Question_1/2_spark/ner_stream.py
   ```

Tab 4. Start Logstash:
   ```
   (Activate venv)
   cd logstash-8.12.1
   bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --group logstash --reset-offsets --to-latest --execute --topic topic2
   ```

Tab 5. Start elasticsearch:
   ```
   cd elasticsearch-8.12.1
   bin/elasticsearch
   ```

Tab 6. Start kibana:
   ```
   cd kibana-8.12.1
   bin/kibana
   ```

Open Kibana to visualize the data (typically at http://localhost:5601)

## Pipeline Flow

1. **Data Ingestion**: The Reddit producer streams comments from r/news to Kafka topic "topic1"
2. **Processing**: The Spark job reads from "topic1", performs NER extraction, aggregates counts, and writes to "topic2"
3. **Storage**: Logstash reads from "topic2" and stores entity counts in Elasticsearch
4. **Visualization**: Kibana dashboards display the entity counts as bar and donut charts

## Visualizations

The project includes visualizations of named entities extracted from Reddit comments:
- Bar plots showing most frequent entities at 15, 30, 45, and 60-minute intervals
- Donut plots showing distribution of top entities at 15, 30, 45, and 60-minute intervals

## Notes

- The NLTK-based NER extractor identifies named entities like people, organizations, and locations.
- Entity counts are aggregated and updated every 30 seconds.
- Visualizations show how entity frequencies change over time, reflecting trending topics on r/news.
