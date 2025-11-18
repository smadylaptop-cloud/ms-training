# ✅ **Detailed Explanation of Your Kafka Service**

```yaml
kafka:
  image: confluentinc/cp-kafka:7.4.0
  container_name: kafka
  ports:
    - "9092:9092"
  environment:
    KAFKA_PROCESS_ROLES: broker,controller
    KAFKA_NODE_ID: 1
    KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:29093
    KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:29093
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
    KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
    KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
    KAFKA_LOG_DIRS: /var/lib/kafka/data
    CLUSTER_ID: "zRh-jDclQJCSxbanIX3Zdw"
    KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
    KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
  volumes:
    - kafka_data:/var/lib/kafka/data
  healthcheck:
    test:
      [
        "CMD",
        "kafka-topics.sh",
        "--bootstrap-server",
        "localhost:9092",
        "--list",
      ]
    interval: 10s
    timeout: 5s
    retries: 5
  networks:
    - micro-net
```

---

# 🔥 **Breakdown by sections**

## **1. image**

```yaml
image: confluentinc/cp-kafka:7.4.0
```

You are using Confluent’s official Kafka image version **7.4.0** which includes:

- Kafka with **KRaft mode** (no ZooKeeper).
- Tools like `kafka-topics.sh`, `kafka-console-producer.sh`, etc.

---

## **2. Container name**

```yaml
container_name: kafka
```

Gives the container an easy-to-reference name `kafka`.

---

## **3. Port mapping**

```yaml
ports:
  - "9092:9092"
```

- Kafka listens internally on `9092`.
- Exposes port `9092` to the host machine.
- Lets your local apps or other microservices connect using:
  **PLAINTEXT://localhost:9092**

---

# ⚙️ **4. Environment Variables (Core of Kafka Setup)**

This section configures **Kafka in KRaft mode (broker + controller)**.

---

## **KAFKA_PROCESS_ROLES**

```yaml
KAFKA_PROCESS_ROLES: broker,controller
```

Kafka normally needs ZooKeeper.
In **KRaft mode**, Kafka can act as:

- **broker** → handles topics, messages
- **controller** → cluster metadata manager

You are running a _single node_ that is **both**.

---

## **KAFKA_NODE_ID**

```yaml
KAFKA_NODE_ID: 1
```

Each Kafka node needs a **unique numeric ID**.
Because you have only one node → **ID = 1**.

---

## **KAFKA_CONTROLLER_QUORUM_VOTERS**

```yaml
KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:29093
```

Defines where the controller quorum is.

Format:

```
<node_id>@<hostname>:<controller_port>
```

Meaning:

- Node 1 is the controller
- Accessible via `kafka:29093` (inside the Docker network)

This is required for KRaft mode.

---

## **KAFKA_LISTENERS**

```yaml
KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:29093
```

Tells Kafka which ports to listen on inside the container:

### **PLAINTEXT listener**

Used by producers and consumers:

```
0.0.0.0:9092
```

### **CONTROLLER listener**

Internal KRaft controller port:

```
0.0.0.0:29093
```

---

## **KAFKA_ADVERTISED_LISTENERS**

```yaml
KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
```

Kafka tells clients **how to reach it**.

- Inside the Docker network, Kafka’s hostname is `kafka`.
- So other containers connect to:

```
PLAINTEXT://kafka:9092
```

This is crucial:
If advertised listeners are wrong, clients CANNOT connect.

---

## **KAFKA_INTER_BROKER_LISTENER_NAME**

```yaml
KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
```

Kafka uses `PLAINTEXT` listener for internal broker communication.
(You only have 1 broker, but still required.)

---

## **KAFKA_CONTROLLER_LISTENER_NAMES**

```yaml
KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
```

Uses the `CONTROLLER` listener for controller quorum communication.

---

## **KAFKA_LOG_DIRS**

```yaml
KAFKA_LOG_DIRS: /var/lib/kafka/data
```

Where Kafka stores:

- Topic partitions
- Offsets
- Cluster metadata
- Controller logs

This directory is persisted via Docker volume.

---

## **CLUSTER_ID**

```yaml
CLUSTER_ID: "zRh-jDclQJCSxbanIX3Zdw"
```

Required in KRaft mode.

Kafka will refuse to start without a pre-created cluster ID.

You can generate a new ID using:

```
kafka-storage.sh random-uuid
```

But since you're using Docker-compose, a fixed ID is ideal.

---

## **KAFKA_AUTO_CREATE_TOPICS_ENABLE**

```yaml
KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
```

Kafka will automatically create topics **when a producer publishes** to a non-existing topic.

Useful for development.

---

## **KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR**

```yaml
KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
```

Because you have only **one broker**, replication factor MUST be:

```
1
```

Otherwise Kafka will refuse to start.

---

# 🗂 **5. Volumes**

```yaml
volumes:
  - kafka_data:/var/lib/kafka/data
```

Persists Kafka data so it is NOT lost when container stops.

---

# ❤️ **6. Healthcheck**

```yaml
healthcheck:
  test:
    ["CMD", "kafka-topics.sh", "--bootstrap-server", "localhost:9092", "--list"]
  interval: 10s
  timeout: 5s
  retries: 5
```

Docker checks if Kafka is responding by listing topics.

If successful → `healthy`
If failed → `unhealthy`

This helps other services wait until Kafka is ready.

---

# 🌐 **7. Network**

```yaml
networks:
  - micro-net
```

Kafka joins the Docker network `micro-net`.
Other microservices can now connect using hostname:

```
kafka:9092
```

---

# 🎉 **Summary (Simplified)**

Your Kafka setup is:

| Component                  | Purpose                        |
| -------------------------- | ------------------------------ |
| KRaft mode                 | No ZooKeeper needed            |
| Single broker + controller | Simple local development       |
| PLAINTEXT listener         | External apps connect to Kafka |
| Controller listener        | Internal KRaft metadata        |
| Persistent volume          | Keep data across restarts      |
| Healthcheck                | Ensures Kafka is alive         |
