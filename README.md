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

---

## 📂 Repo structure

- `infra/` – Docker Compose configs for Kafka, Zookeeper, and Cassandra  
- `producer/` – Python app that streams Wikimedia “recentchange” events into Kafka  
- `processing/` – *Coming soon*: Spark Structured Streaming job  
- `dashboard/` – *Coming soon*: Visualization layer (Grafana or React)  
- `docs/` – Architecture diagrams, design notes, and documentation

---

## 🛠️ Prerequisites

- Docker & Docker Desktop (with WSL2 integration on Windows)  
- Python 3.8+  
- (Optional) VS Code with the Remote – WSL extension for editing under WSL

---

## 🔍 Next Steps

- Scaffold and run the Spark Structured Streaming job in `processing/`  
- Build the dashboard in `dashboard/`
