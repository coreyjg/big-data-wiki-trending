# big-data-wiki-trending

Real-time Trending Wikipedia Topics Pipeline using Kafka, Spark Structured Streaming, Cassandra & Docker

---

## 🚀 Quickstart

1. **Clone the repo**  
   ```bash
   git clone https://github.com/coreyjg/big-data-wiki-trending.git
   cd big-data-wiki-trending
   ```

2. **Bring up the infrastructure**  
   ```bash
   cd infra
   docker compose up -d
   ```

3. **Start the producer** (in a new shell)  
   ```bash
   cd producer
   source .venv/bin/activate  # activate the Python virtual environment
   ./wiki_producer.py
   ```

4. **Start the Spark streaming job** (in another shell)
```bash
cd processing
export \
  KAFKA_BOOTSTRAP_SERVERS=localhost:9092 \
  KAFKA_TOPIC=wiki.pageviews \
  CASSANDRA_HOST=127.0.0.1 \
  CASSANDRA_USER=cassandra \
  CASSANDRA_PASS=cassandra \
  CHECKPOINT_LOCATION=/tmp/wiki_cassandra_ckpt

spark-submit \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,com.datastax.spark:spark-cassandra-connector_2.12:3.2.0 \
  spark_stream.py
  ```
---

## 📂 Repo structure

- `infra/` – Docker Compose configs for Kafka, Zookeeper, and Cassandra  
- `producer/` – Python app that streams Wikimedia “recentchange” events into Kafka  
- `processing/` – Spark Structured Streaming job that reads from Kafka, aggregates pageview counts, and writes to Cassandra  
- `dashboard/` – *Coming soon*: Visualization layer (Grafana or React)  
- `docs/` – Architecture diagrams, design notes, and documentation

---

## 🛠️ Prerequisites

- Docker & Docker Desktop (with WSL2 integration on Windows)  
- Python 3.8+  
- (Optional) VS Code with the Remote – WSL extension for editing under WSL

---

## 🔍 Next Steps

### 🛠️ Harden the streaming job

- Add graceful shutdown handling (e.g. trap SIGTERM → `query.stop()`)
- Externalize any remaining hard-coded settings and add validation
- Bake in your chosen log-level (you’ve set it to `WARN` in code)

### 📈 Deploy & monitor

- Stand up Prometheus/Grafana to surface Kafka, Spark and Cassandra health
- Hook up alerting on missed micro-batches or Cassandra write failures

### 📊 Build the dashboard in `dashboard/`

- Sketch out key views (e.g. “Top trending pages,” “Throughput over time”)
- Wire up your Cassandra backend to a Grafana data source or React UI

### ✅ Testing & CI/CD

- Add unit/integration tests for both the producer and streaming job
- Configure a GitHub Action to lint/format, run tests, and lint your Docker setup on every PR

### 📚 Documentation

- Flesh out `docs/` with deployment & scaling guides
- Capture operational runbooks for “how to recover” and “how to upgrade”

### 🚀 Productionize

- Containerize `spark_stream.py` and/or package as a JAR for your clusters
- Tune Spark/Cassandra resource configs for your expected data volume