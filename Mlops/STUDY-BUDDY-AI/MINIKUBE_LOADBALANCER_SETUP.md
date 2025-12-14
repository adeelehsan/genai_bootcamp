# LoadBalancer Setup for Minikube on GCP

## Overview

Minikube doesn't have native cloud LoadBalancer support like GKE. However, we have several options:

1. **MetalLB** - Software load balancer for bare-metal Kubernetes
2. **Nginx Reverse Proxy** - External load balancer on the host
3. **GCP Load Balancer** - Proper cloud load balancer (most production-ready)

---

## Option 1: MetalLB (Recommended for Minikube)

MetalLB provides LoadBalancer implementation for bare-metal Kubernetes clusters.

### Step 1: Enable MetalLB in Minikube

```bash
# SSH into your GCP instance
gcloud compute ssh instance-20251213-180737 --zone=YOUR_ZONE

# Enable MetalLB addon
minikube addons enable metallb
```

### Step 2: Configure MetalLB IP Range

```bash
# Get Minikube IP range
minikube ip
# Example output: 192.168.49.2

# Configure MetalLB with IP range
# Use IPs in the same subnet as Minikube
minikube addons configure metallb
# When prompted, enter:
# Start IP: 192.168.49.100
# End IP: 192.168.49.110
```

Or configure via YAML:

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  namespace: metallb-system
  name: config
data:
  config: |
    address-pools:
    - name: default
      protocol: layer2
      addresses:
      - 192.168.49.100-192.168.49.110
EOF
```

### Step 3: Change ArgoCD Service to LoadBalancer

```bash
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'

# Wait and check external IP
kubectl get svc argocd-server -n argocd --watch
```

You should see an EXTERNAL-IP like `192.168.49.100`.

### Step 4: Port Forward to Access from Outside

Since MetalLB IP is still internal to Minikube, use `socat` or port-forward:

```bash
# Install socat
sudo apt-get update && sudo apt-get install -y socat

# Get the LoadBalancer IP
LB_IP=$(kubectl get svc argocd-server -n argocd -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Forward HTTP port
sudo socat TCP-LISTEN:80,fork,reuseaddr TCP:${LB_IP}:80 &

# Forward HTTPS port
sudo socat TCP-LISTEN:443,fork,reuseaddr TCP:${LB_IP}:443 &
```

### Step 5: Create GCP Firewall Rules

```bash
# From your local machine
gcloud compute firewall-rules create allow-argocd-lb \
    --allow tcp:80,tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow ArgoCD via LoadBalancer"
```

### Step 6: Access ArgoCD

```
http://34.171.44.90
https://34.171.44.90
```

---

## Option 2: Nginx Reverse Proxy (Production-Ready)

Set up Nginx on the GCP instance as a reverse proxy to Minikube services.

### Step 1: Install Nginx

```bash
# SSH into your GCP instance
gcloud compute ssh instance-20251213-180737 --zone=YOUR_ZONE

# Install Nginx
sudo apt-get update
sudo apt-get install -y nginx
```

### Step 2: Configure Nginx as Reverse Proxy

```bash
# Get ArgoCD service ClusterIP
ARGOCD_IP=$(kubectl get svc argocd-server -n argocd -o jsonpath='{.spec.clusterIP}')

# Create Nginx config
sudo tee /etc/nginx/sites-available/argocd > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://$(minikube ip):31513;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

server {
    listen 443 ssl;
    server_name _;

    # Self-signed certificate (for testing)
    ssl_certificate /etc/ssl/certs/ssl-cert-snakeoil.pem;
    ssl_certificate_key /etc/ssl/private/ssl-cert-snakeoil.key;

    location / {
        proxy_pass https://$(minikube ip):30529;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_ssl_verify off;
    }
}
EOF

# Enable the config
sudo ln -sf /etc/nginx/sites-available/argocd /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and reload Nginx
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl enable nginx
```

### Step 3: Create Firewall Rules

```bash
# From your local machine
gcloud compute firewall-rules create allow-nginx \
    --allow tcp:80,tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow Nginx reverse proxy"
```

### Step 4: Access ArgoCD

```
http://34.171.44.90
https://34.171.44.90
```

**Advantages:**
- ✅ Production-ready
- ✅ Can add SSL/TLS certificates
- ✅ Can add authentication
- ✅ Can load balance multiple backends

---

## Option 3: GCP Load Balancer (Most Production-Ready)

Use GCP's native Load Balancer to route traffic to your Minikube instance.

### Architecture

```
Internet → GCP Load Balancer → GCP VM (Nginx) → Minikube → ArgoCD
```

### Step 1: Set Up Instance Group

```bash
# From your local machine

# Create instance group with your VM
gcloud compute instance-groups unmanaged create argocd-ig \
    --zone=YOUR_ZONE

# Add your instance to the group
gcloud compute instance-groups unmanaged add-instances argocd-ig \
    --zone=YOUR_ZONE \
    --instances=instance-20251213-180737
```

### Step 2: Create Health Check

```bash
gcloud compute health-checks create http argocd-health-check \
    --port=80 \
    --request-path=/
```

### Step 3: Create Backend Service

```bash
gcloud compute backend-services create argocd-backend \
    --protocol=HTTP \
    --health-checks=argocd-health-check \
    --global

# Add instance group to backend
gcloud compute backend-services add-backend argocd-backend \
    --instance-group=argocd-ig \
    --instance-group-zone=YOUR_ZONE \
    --global
```

### Step 4: Create URL Map

```bash
gcloud compute url-maps create argocd-url-map \
    --default-service=argocd-backend
```

### Step 5: Create HTTP(S) Proxy

```bash
# For HTTP
gcloud compute target-http-proxies create argocd-http-proxy \
    --url-map=argocd-url-map

# For HTTPS (requires SSL certificate)
# First, create a managed SSL certificate
gcloud compute ssl-certificates create argocd-cert \
    --domains=argocd.yourdomain.com

gcloud compute target-https-proxies create argocd-https-proxy \
    --ssl-certificates=argocd-cert \
    --url-map=argocd-url-map
```

### Step 6: Create Forwarding Rules (Get External IP)

```bash
# Reserve static IP
gcloud compute addresses create argocd-ip --global

# Get the IP
gcloud compute addresses describe argocd-ip --global

# Create forwarding rule for HTTP
gcloud compute forwarding-rules create argocd-http-rule \
    --address=argocd-ip \
    --global \
    --target-http-proxy=argocd-http-proxy \
    --ports=80

# Create forwarding rule for HTTPS
gcloud compute forwarding-rules create argocd-https-rule \
    --address=argocd-ip \
    --global \
    --target-https-proxy=argocd-https-proxy \
    --ports=443
```

### Step 7: Configure Nginx on Instance

Still need Nginx on the instance to route to Minikube (use Option 2 config above).

### Step 8: Access ArgoCD

```bash
# Get your load balancer IP
gcloud compute addresses describe argocd-ip --global --format='get(address)'

# Access via this IP
http://<LOAD_BALANCER_IP>
https://<LOAD_BALANCER_IP>
```

**Advantages:**
- ✅ Most production-ready
- ✅ Global load balancing
- ✅ Auto SSL certificates
- ✅ DDoS protection
- ✅ Health checks and auto-healing

**Disadvantages:**
- ❌ More expensive (~$18/month + traffic costs)
- ❌ More complex setup

---

## Option 4: Minikube Tunnel + HAProxy

Use Minikube tunnel with HAProxy for load balancing.

### Step 1: Start Minikube Tunnel

```bash
# SSH into GCP instance
gcloud compute ssh instance-20251213-180737 --zone=YOUR_ZONE

# Start tunnel in background
nohup sudo minikube tunnel > /tmp/minikube-tunnel.log 2>&1 &

# Change ArgoCD to LoadBalancer
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'

# Get the external IP
kubectl get svc argocd-server -n argocd
# Should show EXTERNAL-IP like 10.96.x.x
```

### Step 2: Install and Configure HAProxy

```bash
sudo apt-get update
sudo apt-get install -y haproxy

# Get LoadBalancer IP
LB_IP=$(kubectl get svc argocd-server -n argocd -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Configure HAProxy
sudo tee /etc/haproxy/haproxy.cfg > /dev/null <<EOF
global
    log /dev/log local0
    log /dev/log local1 notice
    daemon

defaults
    log global
    mode http
    option httplog
    timeout connect 5000
    timeout client  50000
    timeout server  50000

frontend http_front
    bind *:80
    default_backend argocd_http

frontend https_front
    bind *:443
    mode tcp
    default_backend argocd_https

backend argocd_http
    server argocd1 ${LB_IP}:80 check

backend argocd_https
    mode tcp
    server argocd1 ${LB_IP}:443 check
EOF

# Restart HAProxy
sudo systemctl restart haproxy
sudo systemctl enable haproxy
```

### Step 3: Create Firewall Rules and Access

```bash
# From local machine
gcloud compute firewall-rules create allow-haproxy \
    --allow tcp:80,tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HAProxy"

# Access
# http://34.171.44.90
# https://34.171.44.90
```

---

## Comparison Table

| Option | Complexity | Cost | Production-Ready | External IP | SSL Support |
|--------|-----------|------|------------------|-------------|-------------|
| MetalLB + socat | Low | Free | ⭐⭐ | GCP Instance IP | Manual |
| Nginx Reverse Proxy | Medium | Free | ⭐⭐⭐⭐ | GCP Instance IP | ✅ |
| GCP Load Balancer | High | $18+/mo | ⭐⭐⭐⭐⭐ | Static Global IP | ✅ Auto |
| Minikube Tunnel + HAProxy | Medium | Free | ⭐⭐⭐ | GCP Instance IP | Manual |

---

## Recommended Solution

**For Development/Testing:**
→ Use **Nginx Reverse Proxy** (Option 2)

**For Production:**
→ Use **GCP Load Balancer** (Option 3)

**For Learning/POC:**
→ Use **MetalLB** (Option 1)

---

## Complete Setup Script (Nginx Reverse Proxy)

Here's a complete automated setup:

```bash
#!/bin/bash

# SSH into your GCP instance first, then run this script

set -e

echo "Installing Nginx..."
sudo apt-get update
sudo apt-get install -y nginx

echo "Getting Minikube IP..."
MINIKUBE_IP=$(minikube ip)
echo "Minikube IP: $MINIKUBE_IP"

echo "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/argocd > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://${MINIKUBE_IP}:31513;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

server {
    listen 443 ssl;
    server_name _;

    ssl_certificate /etc/ssl/certs/ssl-cert-snakeoil.pem;
    ssl_certificate_key /etc/ssl/private/ssl-cert-snakeoil.key;

    location / {
        proxy_pass https://${MINIKUBE_IP}:30529;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_ssl_verify off;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

echo "Enabling Nginx config..."
sudo ln -sf /etc/nginx/sites-available/argocd /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

echo "Testing Nginx config..."
sudo nginx -t

echo "Restarting Nginx..."
sudo systemctl restart nginx
sudo systemctl enable nginx

echo "Getting external IP..."
EXTERNAL_IP=$(curl -s ifconfig.me)

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo "Access ArgoCD at:"
echo "HTTP:  http://${EXTERNAL_IP}"
echo "HTTPS: https://${EXTERNAL_IP}"
echo ""
echo "Don't forget to create firewall rules:"
echo "gcloud compute firewall-rules create allow-argocd \\"
echo "    --allow tcp:80,tcp:443 \\"
echo "    --source-ranges 0.0.0.0/0 \\"
echo "    --description 'Allow ArgoCD access'"
echo "======================================"
```

Save this as `setup-argocd-lb.sh` and run:

```bash
chmod +x setup-argocd-lb.sh
./setup-argocd-lb.sh
```

---

## Troubleshooting

### Issue: Nginx can't connect to Minikube

```bash
# Test connectivity
curl http://$(minikube ip):31513

# Check Minikube status
minikube status

# Restart Minikube
minikube stop && minikube start
```

### Issue: 502 Bad Gateway

```bash
# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Check if ArgoCD is running
kubectl get pods -n argocd
```

### Issue: Can't access from browser

```bash
# Verify firewall rules
gcloud compute firewall-rules list | grep -E "80|443"

# Test locally
curl http://localhost

# Check Nginx is running
sudo systemctl status nginx
```

---

## Security Enhancements

### 1. Add SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install -y certbot python3-certbot-nginx

# Get certificate (requires domain name)
sudo certbot --nginx -d argocd.yourdomain.com
```

### 2. Add Basic Authentication

```bash
# Install apache2-utils
sudo apt-get install -y apache2-utils

# Create password file
sudo htpasswd -c /etc/nginx/.htpasswd admin

# Update Nginx config
sudo nano /etc/nginx/sites-available/argocd
# Add these lines inside location block:
#     auth_basic "Restricted Access";
#     auth_basic_user_file /etc/nginx/.htpasswd;
```

### 3. IP Whitelisting

```bash
# Update Nginx config to allow only specific IPs
# Add inside location block:
#     allow YOUR_IP_ADDRESS;
#     deny all;
```

---

## Monitoring

### Check Nginx Access Logs

```bash
sudo tail -f /var/log/nginx/access.log
```

### Check Nginx Status

```bash
curl http://localhost/nginx_status
```

### Monitor Connections

```bash
sudo netstat -tulpn | grep nginx
```
