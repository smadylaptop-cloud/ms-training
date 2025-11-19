## **One-Day Kubernetes Microservices Training Outline**

#### **1. Introduction to Kubernetes**

- What is Kubernetes (K8s)?

  - Container orchestration platform.
  - Manages containerized applications across multiple hosts.

- Key Concepts:

  - **Pod**: Smallest deployable unit in K8s, can contain 1+ containers.
  - **Deployment**: Manages pods, ensures desired replicas.
  - **Service**: Exposes pods to the network.
  - **Namespace**: Isolates resources.
  - **ConfigMap / Secret**: Store configuration and sensitive data.

- Why Kubernetes?

  - Scaling, self-healing, rolling updates, service discovery.

#### **2. Installing Kubernetes on WSL with Minikube**

- Verify Docker is running:

```bash
docker --version
```

- Start Minikube (you already did this):

```bash
minikube start --driver=docker
```

- Verify status:

```bash
minikube status
kubectl cluster-info
kubectl get nodes
```

- Install `kubectl` if not already:

```bash
sudo apt update
sudo apt install -y kubectl
kubectl version --client
```

#### **3. Minikube Essentials**

- Enable dashboard:

```bash
minikube dashboard
```

- Minikube Docker environment (build images directly inside Minikube):

```bash
eval $(minikube docker-env)
```

- Common commands:

  - `kubectl get pods`
  - `kubectl get services`
  - `kubectl describe pod <pod-name>`
  - `kubectl logs <pod-name>`

---

### **Midday Session: Hands-on Python Microservices**

#### **1. Python Microservices Overview**

- Two microservices:

  1. **User Service**: Manages users.
  2. **Order Service**: Manages orders and talks to User Service.

#### **2. Project Structure**

```
microservices-k8s/
│
├─ user_service/
│  ├─ app.py
│  ├─ requirements.txt
│  └─ Dockerfile
│
├─ order_service/
│  ├─ app.py
│  ├─ requirements.txt
│  └─ Dockerfile
│
└─ k8s/
   ├─ user-deployment.yaml
   ├─ user-service.yaml
   ├─ order-deployment.yaml
   └─ order-service.yaml
```

---

#### **3. User Service (Python / Flask)**

**`user_service/app.py`**

```python
from flask import Flask, jsonify

app = Flask(__name__)

users = [
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"},
    {"id": 3, "name": "Charlie"}
]

@app.route("/users", methods=["GET"])
def get_users():
    return jsonify(users), 200

@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = next((u for u in users if u["id"] == user_id), None)
    if user:
        return jsonify(user), 200
    return jsonify({"message": "User not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

**`user_service/requirements.txt`**

```
Flask==2.3.3
```

**`user_service/Dockerfile`**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

---

#### **4. Order Service (Python / Flask)**

**`order_service/app.py`**

```python
from flask import Flask, jsonify
import requests
import os

app = Flask(__name__)

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:5000/users")

orders = [
    {"id": 1, "user_id": 1, "item": "Laptop"},
    {"id": 2, "user_id": 2, "item": "Phone"}
]

@app.route("/orders", methods=["GET"])
def get_orders():
    return jsonify(orders), 200

@app.route("/orders/<int:user_id>", methods=["GET"])
def get_user_orders(user_id):
    user_resp = requests.get(f"{USER_SERVICE_URL}/{user_id}")
    if user_resp.status_code != 200:
        return jsonify({"message": "User not found"}), 404

    user_orders = [o for o in orders if o["user_id"] == user_id]
    return jsonify(user_orders), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
```

**`order_service/requirements.txt`**

```
Flask==2.3.3
requests==2.32.1
```

**`order_service/Dockerfile`**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

---

### **Afternoon Session: Kubernetes Deployment**

#### **1. Build Docker images**

```bash
# Inside microservices-k8s/
docker build -t user-service:1.0 ./user_service
docker build -t order-service:1.0 ./order_service
```

> **Tip:** Because we’re in Minikube, use `eval $(minikube docker-env)` before building, so images are directly available to the cluster.

---

#### **2. Kubernetes Deployment YAMLs**

**`k8s/user-deployment.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-deployment
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
          image: user-service:1.0
          ports:
            - containerPort: 5000
```

**`k8s/user-service.yaml`**

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
      port: 5000
      targetPort: 5000
  type: ClusterIP
```

**`k8s/order-deployment.yaml`**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-deployment
spec:
  replicas: 2
  selector:
    matchLabels:
      app: order-service
  template:
    metadata:
      labels:
        app: order-service
    spec:
      containers:
        - name: order-service
          image: order-service:1.0
          ports:
            - containerPort: 5001
          env:
            - name: USER_SERVICE_URL
              value: "http://user-service:5000/users"
```

**`k8s/order-service.yaml`**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: order-service
spec:
  selector:
    app: order-service
  ports:
    - protocol: TCP
      port: 5001
      targetPort: 5001
  type: NodePort
```

---

#### **3. Deploy Services**

```bash
kubectl apply -f k8s/user-deployment.yaml
kubectl apply -f k8s/user-service.yaml
kubectl apply -f k8s/order-deployment.yaml
kubectl apply -f k8s/order-service.yaml

kubectl get pods
kubectl get svc
```

---

#### **4. Test Services**

- Get Minikube IP:

```bash
minikube ip
```

- Access Order Service:

```bash
curl http://<MINIKUBE_IP>:<NODEPORT>/orders/1
```

> **Explanation:**

- `NodePort` exposes the service outside the cluster.
- `ClusterIP` allows internal communication between services (`Order Service` talks to `User Service`).

---

### **Evening Session: Management + Scaling + Cleanup**

#### **1. Scaling Deployments**

```bash
kubectl scale deployment user-deployment --replicas=4
kubectl get pods
```

#### **2. Updating Deployments**

- Change container image, apply deployment → Rolling Update.

#### **3. Debugging**

```bash
kubectl logs <pod-name>
kubectl describe pod <pod-name>
kubectl exec -it <pod-name> -- /bin/sh
```

#### **4. Cleanup**

```bash
kubectl delete -f k8s/order-service.yaml
kubectl delete -f k8s/order-deployment.yaml
kubectl delete -f k8s/user-service.yaml
kubectl delete -f k8s/user-deployment.yaml
minikube stop
minikube delete
```
