#!/usr/bin/env python3
"""
Real-time Wikipedia Pageviews Producer

This script connects to the Wikimedia SSE pageviews stream,
filters for English Wikipedia events, and produces them
to a Kafka topic using the Confluent Kafka Python client.
"""

import json
import requests
from confluent_kafka import Producer

# --- Kafka Producer Configuration ---
# Set up the connection details for the local Kafka broker.
conf = {
    'bootstrap.servers': 'localhost:9092'
}
producer = Producer(conf)  # Confluent Kafka producer instance

# Define the Kafka topic and the SSE stream URL
topic = 'wiki.pageviews'
stream_url = 'https://stream.wikimedia.org/v2/stream/recentchange'

def delivery_report(err, msg):
    """
    Callback function called once for each produced message to report delivery result.
    'err' is an error if delivery failed, otherwise msg contains metadata.
    """
    if err:
        print(f"❌ Message delivery failed: {err}")
    else:
        print(f"✅ Delivered to {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}")

# --- Server-Sent Events (SSE) Helper ---
def sse_events(url):
    """
    Generator that yields full SSE event blocks from the given URL.
    Combines lines until a blank line is encountered, indicating end of event.
    Sends the proper Accept header so the server returns an SSE stream.
    """
    headers = {'Accept': 'text/event-stream'} # Request SSE format
    resp = requests.get(url, headers=headers, stream=True)
    if resp.status_code != 200:
        raise RuntimeError(f"Failed to connect to SSE stream: HTTP {resp.status_code}")
    buffer = ""
    for line in resp.iter_lines(decode_unicode=True):
        if line:
            # Append non-empty lines to the buffer
            buffer += line + "\n"
        else:
            # Blank line signals the end of one event block
            yield buffer
            buffer = ""
    # Yield any remaining buffer content
    if buffer:
        yield buffer

# --- Main Producer Logic ---
def main():
    """
    Main entry point of the producer script.
    - Streams events from Wikimedia.
    - Parses and filters events.
    - Produces filtered events to Kafka.
    """
    print(f"Starting producer → topic '{topic}'")
    # Iterate over each complete SSE event block
    for event in sse_events(stream_url):
        # Split the block into individual lines
        for ln in event.splitlines():
            # Process only the data lines which contain the JSON payload
            if ln.startswith("data:"):
                payload = ln[len("data:"):].strip()
                try:
                    data = json.loads(payload)
                except json.JSONDecodeError:
                    # Skip invalid JSON payloads
                    continue
                # Filter for English Wikipedia edits (recent changes)
                # The 'wiki' field indicates the project, e.g. 'enwiki' for English Wikipedia
                if data.get("wiki", "") == "enwiki":
                    # Produce the JSON payload to the Kafka topic
                    producer.produce(
                        topic,
                        json.dumps(data).encode("utf-8"),
                        callback=delivery_report
                    )
                    # Serve delivery report callbacks
                    producer.poll(0)
    # Ensure all messages are delivered before exiting
    producer.flush()

if __name__ == "__main__":
    main()
