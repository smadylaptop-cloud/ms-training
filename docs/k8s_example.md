### **1. Pod**

A Pod running a simple `nginx` container:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  containers:
    - name: nginx-container
      image: nginx:latest
      ports:
        - containerPort: 80
```

---

### **2. Service**

Expose the Pod via a ClusterIP service:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  selector:
    app: nginx
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
  type: ClusterIP
```

> Note: The Pod should have a label `app: nginx` for this to work.

---

### **3. Deployment**

Deployment with 3 replicas of an nginx Pod:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
        - name: nginx-container
          image: nginx:latest
          ports:
            - containerPort: 80
```

---

### **4. Namespace**

A separate namespace for isolation:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: my-namespace
```

> You can create resources inside this namespace by adding `namespace: my-namespace` under `metadata`.

---

### **5. ConfigMap**

Store non-sensitive configuration data:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: my-config
data:
  APP_ENV: production
  APP_DEBUG: "false"
```

> Pods can reference it as environment variables.

---

### **6. Secret**

Store sensitive data (like passwords):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: my-secret
type: Opaque
stringData:
  DB_PASSWORD: "mypassword123"
```

> Pods can mount this or use it as environment variables.

---

### **7. ReplicaSet**

ReplicaSet managing 2 Pods of nginx:

```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: my-replicaset
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
        - name: nginx
          image: nginx:latest
```

> Normally, Deployment manages ReplicaSets, but you can create it standalone.

---

### **8. Ingress**

Expose a service externally using HTTP:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
spec:
  rules:
    - host: myapp.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: my-service
                port:
                  number: 80
```

> Requires an ingress controller like NGINX Ingress to work.

---

### **9. Volume**

Pod using a PersistentVolumeClaim:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: my-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: pod-with-volume
spec:
  containers:
    - name: nginx
      image: nginx
      volumeMounts:
        - mountPath: "/usr/share/nginx/html"
          name: my-volume
  volumes:
    - name: my-volume
      persistentVolumeClaim:
        claimName: my-pvc
```

Let’s create a **complete working example** that demonstrates all the objects together in one Kubernetes cluster. I’ll make it simple, so you can `kubectl apply -f all-in-one.yaml` and see it work.

---

```yaml
# ---------------- Namespace ----------------
apiVersion: v1
kind: Namespace
metadata:
  name: demo-namespace
---
# ---------------- ConfigMap ----------------
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: demo-namespace
data:
  APP_ENV: production
  APP_DEBUG: "false"
---
# ---------------- Secret ----------------
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
  namespace: demo-namespace
type: Opaque
stringData:
  DB_PASSWORD: "mypassword123"
---
# ---------------- PersistentVolumeClaim ----------------
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-pvc
  namespace: demo-namespace
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
---
# ---------------- Deployment ----------------
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  namespace: demo-namespace
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
        - name: nginx
          image: nginx:latest
          ports:
            - containerPort: 80
          env:
            - name: APP_ENV
              valueFrom:
                configMapKeyRef:
                  name: app-config
                  key: APP_ENV
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: app-secret
                  key: DB_PASSWORD
          volumeMounts:
            - name: storage
              mountPath: /usr/share/nginx/html
      volumes:
        - name: storage
          persistentVolumeClaim:
            claimName: app-pvc
---
# ---------------- Service ----------------
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
  namespace: demo-namespace
spec:
  selector:
    app: nginx
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
  type: ClusterIP
---
# ---------------- Ingress ----------------
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nginx-ingress
  namespace: demo-namespace
spec:
  rules:
    - host: demo.local
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: nginx-service
                port:
                  number: 80
---
# ---------------- Standalone Pod ----------------
apiVersion: v1
kind: Pod
metadata:
  name: standalone-pod
  namespace: demo-namespace
  labels:
    app: nginx
spec:
  containers:
    - name: nginx
      image: nginx:latest
      ports:
        - containerPort: 80
```

---

### ✅ What this manifest does:

1. Creates a **namespace** `demo-namespace`.
2. Adds a **ConfigMap** and **Secret** and mounts them in the Deployment as environment variables.
3. Creates a **PersistentVolumeClaim** and mounts it in the Deployment pod.
4. Deploys **2 replicas** of nginx using a **Deployment**.
5. Exposes the Deployment via a **ClusterIP Service**.
6. Creates an **Ingress** to route HTTP traffic to the service.
7. Creates a **standalone Pod** to demonstrate a pod outside a deployment.

---

### How to apply:

```bash
kubectl apply -f all-in-one.yaml
kubectl get all -n demo-namespace
kubectl describe ingress nginx-ingress -n demo-namespace
```

> If you want the **Ingress to work locally**, you need to edit `/etc/hosts` to point `demo.local` to your Minikube IP:

```bash
minikube ip
```
