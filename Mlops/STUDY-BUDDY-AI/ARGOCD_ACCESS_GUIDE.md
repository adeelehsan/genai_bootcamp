# ArgoCD Access Guide on GCP

## Method 1: NodePort Service (Recommended for GCP)

### Step 1: Check Current ArgoCD Service

```bash
kubectl get svc -n argocd
```

Look for `argocd-server` service and note its type (ClusterIP, NodePort, or LoadBalancer).

### Step 2: Change to NodePort (if currently ClusterIP)

```bash
# Edit the argocd-server service
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "NodePort"}}'
```

### Step 3: Get NodePort Number

```bash
kubectl get svc argocd-server -n argocd -o jsonpath='{.spec.ports[0].nodePort}'
```

This will return a port number like `31704`, `30080`, etc.

### Step 4: Access ArgoCD in Browser

```
https://<GCP_INSTANCE_PUBLIC_IP>:<NODE_PORT>
```

**Example:**
```
https://34.45.193.5:31704
```

### Step 5: Get Admin Password

```bash
# Get the initial admin password
kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" | base64 -d
```

**Login Credentials:**
- Username: `admin`
- Password: (from command above)

---

## Method 2: LoadBalancer Service (Automatic External IP)

### Step 1: Change to LoadBalancer Type

```bash
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'
```

### Step 2: Wait for External IP

```bash
kubectl get svc argocd-server -n argocd --watch
```

Wait until `EXTERNAL-IP` shows an IP address (not `<pending>`).

### Step 3: Access ArgoCD

```
https://<EXTERNAL_IP>
```

**Note:** GCP will provision a Load Balancer which incurs additional costs.

---

## Method 3: Ingress with Domain (Production Ready)

### Prerequisites
- Domain name pointing to your GCP instance
- Nginx Ingress Controller installed

### Step 1: Install Nginx Ingress Controller

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml
```

### Step 2: Create ArgoCD Ingress

Create `argocd-ingress.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: argocd-server-ingress
  namespace: argocd
  annotations:
    nginx.ingress.kubernetes.io/ssl-passthrough: "true"
    nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"
spec:
  ingressClassName: nginx
  rules:
  - host: argocd.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: argocd-server
            port:
              number: 443
```

Apply it:
```bash
kubectl apply -f argocd-ingress.yaml
```

### Step 3: Access via Domain

```
https://argocd.yourdomain.com
```

---

## GCP Firewall Rule Configuration

### Check Existing Firewall Rules

```bash
gcloud compute firewall-rules list
```

### Create Firewall Rule for ArgoCD NodePort

```bash
# For specific NodePort (recommended)
gcloud compute firewall-rules create allow-argocd-nodeport \
    --allow tcp:30000-32767 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow ArgoCD NodePort access"

# Or for specific port only
gcloud compute firewall-rules create allow-argocd-31704 \
    --allow tcp:31704 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow ArgoCD access on port 31704"
```

### Verify Firewall Rules

```bash
gcloud compute firewall-rules describe allow-argocd-nodeport
```

---

## Troubleshooting

### Issue 1: "Connection Refused" or "Cannot Connect"

**Check 1: Verify ArgoCD is running**
```bash
kubectl get pods -n argocd
```
All pods should be in `Running` state.

**Check 2: Verify service is NodePort**
```bash
kubectl get svc argocd-server -n argocd
```

**Check 3: Check firewall rules**
```bash
gcloud compute firewall-rules list | grep argocd
```

**Check 4: Verify node port is accessible**
```bash
# SSH into your GCP instance
nc -zv localhost <NODE_PORT>
```

### Issue 2: "SSL/TLS Certificate Error"

This is normal for ArgoCD. You can:

**Option A:** Accept the self-signed certificate (click "Advanced" → "Proceed")

**Option B:** Disable TLS (not recommended for production)
```bash
kubectl patch svc argocd-server -n argocd -p '{"spec": {"ports": [{"port": 80, "targetPort": 8080, "nodePort": 30080}]}}'
```

Then access via HTTP: `http://<IP>:30080`

### Issue 3: "Forgot Admin Password"

**Reset password:**
```bash
# Delete the secret
kubectl delete secret argocd-initial-admin-secret -n argocd

# Restart argocd-server to regenerate
kubectl rollout restart deployment argocd-server -n argocd

# Get new password
kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" | base64 -d
```

### Issue 4: Can't Access from Browser but kubectl works

**Check GCP Network Tags:**
```bash
# List your instance
gcloud compute instances list

# Describe instance to see network tags
gcloud compute instances describe YOUR_INSTANCE_NAME --zone=YOUR_ZONE

# Add network tags if needed
gcloud compute instances add-tags YOUR_INSTANCE_NAME \
    --zone=YOUR_ZONE \
    --tags=http-server,https-server,argocd-server
```

---

## Security Best Practices

### 1. Restrict Source IP (Recommended)

Instead of `0.0.0.0/0`, restrict to your IP:

```bash
gcloud compute firewall-rules update allow-argocd-nodeport \
    --source-ranges YOUR_IP_ADDRESS/32
```

Get your IP:
```bash
curl ifconfig.me
```

### 2. Use Strong Password

```bash
# Update admin password
argocd account update-password
```

### 3. Enable MFA (Multi-Factor Authentication)

Follow ArgoCD documentation to enable OIDC or LDAP with MFA.

### 4. Use HTTPS Only

Never disable TLS in production. Use proper certificates with Let's Encrypt or Cloud Certificate Manager.

---

## Quick Access Commands

### Get Everything You Need

```bash
# Get NodePort
echo "NodePort: $(kubectl get svc argocd-server -n argocd -o jsonpath='{.spec.ports[0].nodePort}')"

# Get Admin Password
echo "Password: $(kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" | base64 -d)"

# Get GCP Instance Public IP
echo "Public IP: $(gcloud compute instances describe YOUR_INSTANCE_NAME --zone=YOUR_ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')"
```

### Complete Access URL

```bash
NODE_PORT=$(kubectl get svc argocd-server -n argocd -o jsonpath='{.spec.ports[0].nodePort}')
PUBLIC_IP=$(gcloud compute instances describe YOUR_INSTANCE_NAME --zone=YOUR_ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
echo "Access ArgoCD at: https://${PUBLIC_IP}:${NODE_PORT}"
```

---

## Common NodePort Ranges

Kubernetes NodePort services use ports in the range **30000-32767**.

Common ArgoCD NodePorts you might see:
- `31704` (common in examples)
- `30080` (HTTP)
- `30443` (HTTPS)
- `32080` (alternative)

---

## Testing Connection

### From Your Local Machine

```bash
# Test if port is open (replace with your IP and port)
nc -zv 34.45.193.5 31704

# Or use telnet
telnet 34.45.193.5 31704

# Or use curl
curl -k https://34.45.193.5:31704
```

### From GCP Instance

```bash
# SSH into instance
gcloud compute ssh YOUR_INSTANCE_NAME --zone=YOUR_ZONE

# Test locally
curl -k https://localhost:<NODE_PORT>

# Test via public IP
curl -k https://<PUBLIC_IP>:<NODE_PORT>
```

---

## Example: Complete Setup Script

```bash
#!/bin/bash

# Variables
NAMESPACE="argocd"
INSTANCE_NAME="your-gke-instance"
ZONE="us-central1-a"

# Step 1: Change service to NodePort
echo "Changing ArgoCD service to NodePort..."
kubectl patch svc argocd-server -n $NAMESPACE -p '{"spec": {"type": "NodePort"}}'

# Step 2: Get NodePort
NODE_PORT=$(kubectl get svc argocd-server -n $NAMESPACE -o jsonpath='{.spec.ports[0].nodePort}')
echo "NodePort: $NODE_PORT"

# Step 3: Create firewall rule
echo "Creating firewall rule..."
gcloud compute firewall-rules create allow-argocd-$NODE_PORT \
    --allow tcp:$NODE_PORT \
    --source-ranges 0.0.0.0/0 \
    --description "Allow ArgoCD access on port $NODE_PORT"

# Step 4: Get public IP
PUBLIC_IP=$(gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

# Step 5: Get admin password
PASSWORD=$(kubectl get secret argocd-initial-admin-secret -n $NAMESPACE -o jsonpath="{.data.password}" | base64 -d)

# Step 6: Display access info
echo ""
echo "======================================"
echo "ArgoCD Access Information"
echo "======================================"
echo "URL: https://${PUBLIC_IP}:${NODE_PORT}"
echo "Username: admin"
echo "Password: ${PASSWORD}"
echo "======================================"
```

Save as `setup-argocd-access.sh`, make it executable, and run:
```bash
chmod +x setup-argocd-access.sh
./setup-argocd-access.sh
```

---

## Monitoring and Logs

### Check ArgoCD Server Logs

```bash
kubectl logs -n argocd deployment/argocd-server -f
```

### Check Service Status

```bash
kubectl get all -n argocd
```

### Check Events

```bash
kubectl get events -n argocd --sort-by='.lastTimestamp'
```

---

## Additional Resources

- [ArgoCD Official Documentation](https://argo-cd.readthedocs.io/)
- [GCP Firewall Rules](https://cloud.google.com/vpc/docs/firewalls)
- [Kubernetes Services](https://kubernetes.io/docs/concepts/services-networking/service/)
