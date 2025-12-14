# ArgoCD Access Troubleshooting Guide

## Issue: Cannot Access ArgoCD at https://34.171.44.90

ArgoCD was working before but now returns connection error or timeout.

---

## Quick Diagnostics

Run these commands on your GCP instance to identify the issue:

```bash
# SSH into your instance
gcloud compute ssh instance-20251213-180737 --zone=YOUR_ZONE

# Then run these checks:
```

### 1. Check ArgoCD Pods Status

```bash
kubectl get pods -n argocd

# All pods should show Running and 1/1 READY
```

**Expected Output:**
```
NAME                                  READY   STATUS    RESTARTS   AGE
argocd-application-controller-xxx     1/1     Running   0          1h
argocd-dex-server-xxx                 1/1     Running   0          1h
argocd-redis-xxx                      1/1     Running   0          1h
argocd-repo-server-xxx                1/1     Running   0          1h
argocd-server-xxx                     1/1     Running   0          1h
```

**If any pod is not Running:**
```bash
# Get pod details
kubectl describe pod <pod-name> -n argocd

# Check logs
kubectl logs <pod-name> -n argocd
```

### 2. Check ArgoCD Service

```bash
kubectl get svc argocd-server -n argocd

# Should show NodePort type with ports
```

**Expected Output:**
```
NAME            TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)                      AGE
argocd-server   NodePort   10.103.167.185  <none>        80:31513/TCP,443:30529/TCP   1h
```

### 3. Check Nginx Status (If Using Nginx)

```bash
# Check if Nginx is running
sudo systemctl status nginx

# Check Nginx error logs
sudo tail -50 /var/log/nginx/error.log

# Check Nginx configuration
sudo nginx -t
```

### 4. Check Port-Forward Processes (If Using Port-Forward)

```bash
# Check if port-forward is running
ps aux | grep port-forward

# Check for any process on port 80/443
sudo netstat -tulpn | grep -E ':80|:443'
```

### 5. Test Local Access

```bash
# Get Minikube IP
minikube ip

# Test ArgoCD on Minikube IP
curl -k http://$(minikube ip):31513

# Test on localhost
curl http://localhost
```

---

## Common Issues and Fixes

### Issue 1: ArgoCD Pods Crashed or Restarting

**Symptoms:**
```bash
kubectl get pods -n argocd
# Shows CrashLoopBackOff or Error
```

**Fix:**
```bash
# Restart ArgoCD deployment
kubectl rollout restart deployment argocd-server -n argocd
kubectl rollout restart deployment argocd-repo-server -n argocd

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s

# Check status
kubectl get pods -n argocd
```

### Issue 2: Nginx Stopped

**Symptoms:**
```bash
sudo systemctl status nginx
# Shows inactive (dead)
```

**Fix:**
```bash
# Start Nginx
sudo systemctl start nginx

# Check status
sudo systemctl status nginx

# Enable on boot
sudo systemctl enable nginx

# Test access
curl http://localhost
```

### Issue 3: Nginx Configuration Error

**Symptoms:**
```bash
sudo nginx -t
# Shows configuration error
```

**Fix:**
```bash
# Check current config
cat /etc/nginx/sites-available/argocd

# Reconfigure Nginx
MINIKUBE_IP=$(minikube ip)

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
        proxy_ssl_verify off;
    }
}
EOF

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

### Issue 4: Port-Forward Process Died

**Symptoms:**
```bash
ps aux | grep port-forward
# Shows no running process
```

**Fix:**
```bash
# Restart port-forward
nohup kubectl port-forward --address 0.0.0.0 service/argocd-server 80:80 443:443 -n argocd > /tmp/argocd-portforward.log 2>&1 &

# Verify it's running
ps aux | grep port-forward

# Test
curl http://localhost
```

### Issue 5: Minikube Stopped or Restarted

**Symptoms:**
```bash
minikube status
# Shows Stopped or minikube ip changed
```

**Fix:**
```bash
# Start Minikube
minikube start

# Wait for it to be ready
kubectl wait --for=condition=ready node --all --timeout=300s

# Check ArgoCD
kubectl get pods -n argocd

# Reconfigure Nginx with new Minikube IP
MINIKUBE_IP=$(minikube ip)
echo "New Minikube IP: $MINIKUBE_IP"

# Update Nginx config (see Issue 3)

# Restart Nginx
sudo systemctl restart nginx
```

### Issue 6: Firewall Rules Changed

**Symptoms:**
Connection times out from external browser

**Fix:**
```bash
# Exit SSH and run from local machine
gcloud compute firewall-rules list | grep -E "80|443|argocd"

# Recreate firewall rules if missing
gcloud compute firewall-rules create allow-argocd-access \
    --allow tcp:80,tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow ArgoCD access"
```

### Issue 7: Certificate/SSL Issues

**Symptoms:**
Browser shows "SSL_ERROR" or "NET::ERR_CERT_INVALID"

**Fix:**
- Click "Advanced" in browser
- Click "Proceed to 34.171.44.90 (unsafe)"

Or use HTTP instead:
```
http://34.171.44.90
```

---

## Complete Reset and Restart

If nothing works, do a complete restart:

```bash
# 1. Check Minikube is running
minikube status
minikube start  # if stopped

# 2. Wait for cluster to be ready
kubectl wait --for=condition=ready node --all --timeout=300s

# 3. Check ArgoCD pods
kubectl get pods -n argocd

# 4. If pods are not ready, restart them
kubectl rollout restart deployment -n argocd

# 5. Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/part-of=argocd -n argocd --timeout=300s

# 6. Get Minikube IP
MINIKUBE_IP=$(minikube ip)
echo "Minikube IP: $MINIKUBE_IP"

# 7. Test ArgoCD directly on Minikube IP
curl -k http://${MINIKUBE_IP}:31513

# 8. If using Nginx, restart it
sudo systemctl restart nginx

# 9. Test localhost
curl http://localhost

# 10. Get external IP
EXTERNAL_IP=$(curl -s ifconfig.me)
echo "Access ArgoCD at: http://${EXTERNAL_IP}"
```

---

## Systematic Diagnostic Script

Save this as `diagnose-argocd.sh`:

```bash
#!/bin/bash

echo "======================================"
echo "ArgoCD Diagnostics"
echo "======================================"
echo ""

# Check Minikube
echo "1. Checking Minikube status..."
minikube status
echo ""

# Check Minikube IP
echo "2. Minikube IP:"
minikube ip
echo ""

# Check ArgoCD pods
echo "3. ArgoCD Pods:"
kubectl get pods -n argocd
echo ""

# Check ArgoCD service
echo "4. ArgoCD Service:"
kubectl get svc argocd-server -n argocd
echo ""

# Check Nginx
echo "5. Nginx Status:"
sudo systemctl status nginx --no-pager | head -5
echo ""

# Check ports
echo "6. Ports in use (80, 443, 31513, 30529):"
sudo netstat -tulpn | grep -E ':80|:443|:31513|:30529'
echo ""

# Check port-forward processes
echo "7. Port-forward processes:"
ps aux | grep port-forward | grep -v grep
echo ""

# Test local access
echo "8. Testing local HTTP access:"
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://localhost/
echo ""

echo "9. Testing Minikube direct access:"
MINIKUBE_IP=$(minikube ip)
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://${MINIKUBE_IP}:31513/
echo ""

# Get external IP
echo "10. External IP:"
curl -s ifconfig.me
echo ""

echo "======================================"
echo "Diagnostics Complete"
echo "======================================"
```

Run it:
```bash
chmod +x diagnose-argocd.sh
./diagnose-argocd.sh
```

---

## Quick Fixes by Setup Type

### If Using Nginx Reverse Proxy:

```bash
# Restart everything
sudo systemctl restart nginx
kubectl rollout restart deployment argocd-server -n argocd

# Wait
sleep 30

# Test
curl http://localhost
```

### If Using Port-Forward:

```bash
# Kill old port-forward
pkill -f "kubectl port-forward.*argocd"

# Start new port-forward
nohup kubectl port-forward --address 0.0.0.0 service/argocd-server 80:80 443:443 -n argocd > /tmp/argocd.log 2>&1 &

# Test
curl http://localhost
```

### If Using NodePort Directly:

```bash
# Test NodePort access
MINIKUBE_IP=$(minikube ip)
curl http://${MINIKUBE_IP}:31513
```

---

## Check Browser/Network Issues

Sometimes the issue is on your local machine:

1. **Clear browser cache**
   - Chrome: Ctrl+Shift+Delete
   - Select "Cached images and files"

2. **Try incognito/private window**

3. **Try different browser**

4. **Check your internet connection**

5. **Try curl from terminal:**
   ```bash
   curl -v http://34.171.44.90
   ```

6. **Ping the server:**
   ```bash
   ping 34.171.44.90
   ```

---

## Get Help

If still not working, provide these outputs:

```bash
# Run on GCP instance
kubectl get pods -n argocd
kubectl get svc argocd-server -n argocd
minikube status
minikube ip
sudo systemctl status nginx
ps aux | grep port-forward
sudo netstat -tulpn | grep -E ':80|:443'
curl -v http://localhost
```

Then share the outputs for further diagnosis.
