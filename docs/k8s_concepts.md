## **1. What is Microservices?**

**Microservices** is an architectural style where an application is built as a collection of **small, independent services**. Each service:

- Handles **one specific business capability**.
- Can be **developed, deployed, and scaled independently**.
- Communicates with other services via **APIs** (usually HTTP/REST or messaging systems like Kafka or RabbitMQ).

**Example:** An e-commerce application could be split into microservices like:

- User Service (manage users)
- Order Service (manage orders)
- Product Service (manage products)
- Payment Service (handle payments)

**Advantages of microservices:**

- Scalability: You can scale only the service that needs more resources.
- Flexibility: Different services can use different programming languages.
- Fault isolation: If one service fails, others can still run.
- Faster deployment: Smaller codebases allow quicker releases.

---

## **2. What is Kubernetes?**

**Kubernetes (K8s)** is an **open-source container orchestration platform**. It manages **containers** across clusters of machines and automates:

- Deployment
- Scaling
- Load balancing
- Rollbacks
- Service discovery

Think of Kubernetes as the “operating system” for your containers.

---

## **3. Kubernetes for Microservices**

Kubernetes is **perfect for microservices** because it can manage multiple small services running in containers, providing:

1. **Service Discovery & Load Balancing**

   - Kubernetes automatically assigns IPs and DNS names for services.
   - It can load balance traffic across multiple pods.

2. **Automated Deployment & Rollback**

   - You can deploy a new version of a microservice without downtime.
   - Rollback to previous versions is easy.

3. **Self-Healing**

   - Failed containers/pods are automatically restarted.
   - Containers that don’t respond are replaced.

4. **Horizontal Scaling**

   - Automatically scale pods up/down based on CPU/memory usage or custom metrics.

5. **Configuration Management & Secrets**

   - Store environment variables, configs, and secrets securely.

---

## **4. Key Kubernetes Concepts / Terminology**

Here are the most common terms:

| Term           | Explanation                                                                                  |
| -------------- | -------------------------------------------------------------------------------------------- |
| **Pod**        | Smallest deployable unit in Kubernetes. Can contain 1+ containers.                           |
| **Service**    | Abstraction to expose pods to network or other services (ClusterIP, NodePort, LoadBalancer). |
| **Deployment** | Ensures a specified number of pod replicas are running and updates them safely.              |
| **Namespace**  | A virtual cluster inside Kubernetes, useful for isolation.                                   |
| **ConfigMap**  | Store non-sensitive configuration data for pods.                                             |
| **Secret**     | Store sensitive data like passwords, API keys.                                               |
| **ReplicaSet** | Ensures a specified number of pod replicas are running. Usually managed by Deployment.       |
| **Ingress**    | Manages external access to services, typically HTTP/HTTPS.                                   |
| **Volume**     | Persistent storage that pods can use.                                                        |

---

## **5. Kubernetes Architecture Overview**

- **Master Node** (Control Plane):

  - **API Server**: Entry point for commands (`kubectl`)
  - **Scheduler**: Assigns pods to nodes
  - **Controller Manager**: Maintains desired state
  - **etcd**: Distributed key-value store for cluster state

- **Worker Node**:

  - **Kubelet**: Communicates with the master, runs pods
  - **Kube-proxy**: Manages network rules for services
  - **Container Runtime**: Runs Docker/containers

---

## **6. Kubernetes Commands (kubectl)**

Here are the most essential commands for beginners:

### **Cluster / Node Info**

```bash
kubectl cluster-info          # Info about master and services
kubectl get nodes             # List all worker nodes
kubectl describe node <node>  # Detailed node info
```

### **Pods**

```bash
kubectl get pods              # List all pods
kubectl describe pod <pod>    # Details of a pod
kubectl logs <pod>            # Get logs from a pod
kubectl exec -it <pod> -- bash # Enter pod shell
```

### **Deployments**

```bash
kubectl get deployments        # List deployments
kubectl create deployment <name> --image=<image>  # Create deployment
kubectl apply -f deployment.yaml                 # Apply YAML file
kubectl scale deployment <name> --replicas=3    # Scale pods
kubectl rollout status deployment/<name>        # Check rollout status
kubectl rollout undo deployment/<name>          # Rollback deployment
```

### **Services**

```bash
kubectl get svc               # List services
kubectl expose deployment <name> --type=NodePort --port=80 --target-port=8000
```

### **Namespaces**

```bash
kubectl get ns                # List namespaces
kubectl create ns <name>      # Create namespace
kubectl delete ns <name>      # Delete namespace
```

### **Delete Resources**

```bash
kubectl delete pod <pod-name>
kubectl delete svc <service-name>
kubectl delete deployment <deployment-name>
```

---

## **7. Kubernetes Microservices Example**

Imagine a simple e-commerce microservice setup:

**Folder structure:**

```
microservices/
├── user-service/
│   └── app.py
├── order-service/
│   └── app.py
├── deployment.yaml
└── service.yaml
```

**deployment.yaml (User Service)**:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
    spec:
      containers:
        - name: user-service
          image: user-service:latest
          ports:
            - containerPort: 5000
```

**service.yaml (Expose User Service)**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: user-service
spec:
  selector:
    app: user-service
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
  type: NodePort
```

Commands to deploy:

```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl get pods
kubectl get svc
```

---

## **8. Summary**

- Microservices = small independent services
- Kubernetes = container orchestration tool
- K8s + Microservices = scalable, fault-tolerant, independent deployment
- Core K8s objects: Pod, Deployment, Service, Namespace
- Commands: `kubectl get`, `kubectl describe`, `kubectl apply`, `kubectl logs`, `kubectl exec`
