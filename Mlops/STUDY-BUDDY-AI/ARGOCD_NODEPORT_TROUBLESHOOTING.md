# ArgoCD NodePort Access Troubleshooting

## Your Situation
- **URL**: http://34.171.44.90:31513/
- **Status**: Can't reach (timeout/connection refused)
- **Port-forward works**: `kubectl port-forward --address 0.0.0.0 service/argocd-server 31704:80 -n argocd` ✅

This means ArgoCD is running fine, but **external NodePort access is blocked**.

---

## Root Cause Analysis

When port-forward works but NodePort doesn't, it's always one of these:

1. **GCP Firewall rules not properly configured** (most common)
2. **Network tags missing on the instance**
3. **Service not actually using NodePort**
4. **Using HTTP instead of HTTPS**

---

## Solution Steps

### Step 1: Verify ArgoCD Service Configuration

```bash
kubectl get svc argocd-server -n argocd -o yaml
```

**Check for:**
- `type: NodePort` (not ClusterIP)
- `nodePort: 31513` (matches your URL)

**Expected output:**
```yaml
spec:
  type: NodePort
  ports:
  - port: 80
    targetPort: 8080
    nodePort: 31513
    protocol: TCP
    name: http
  - port: 443
    targetPort: 8080
    nodePort: XXXXX
    protocol: TCP
    name: https
```

### Step 2: Check GCP Firewall Rules

```bash
# List all firewall rules
gcloud compute firewall-rules list

# Check specific rule (replace with your rule name)
gcloud compute firewall-rules describe RULE_NAME
```

**Common issues:**
- Rule exists but doesn't target your instance
- Rule has wrong port range
- Rule has wrong source IP ranges

### Step 3: Verify Firewall Rule Applies to Your Instance

```bash
# Get your instance details
gcloud compute instances describe YOUR_INSTANCE_NAME --zone=YOUR_ZONE

# Check network tags
gcloud compute instances describe YOUR_INSTANCE_NAME --zone=YOUR_ZONE --format='get(tags.items[])'
```

**Firewall rules apply based on:**
- Network tags
- Target instances
- Service accounts

### Step 4: Create Correct Firewall Rule

```bash
# Get your instance name and zone first
gcloud compute instances list

# Create firewall rule for NodePort range
gcloud compute firewall-rules create allow-k8s-nodeport \
    --allow tcp:30000-32767 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow Kubernetes NodePort services" \
    --direction INGRESS \
    --priority 1000

# Or for specific port only
gcloud compute firewall-rules create allow-argocd-31513 \
    --allow tcp:31513 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow ArgoCD NodePort 31513" \
    --direction INGRESS
```

### Step 5: Apply Network Tag to Instance (if needed)

If your firewall rule uses target tags:

```bash
# Add network tag to your instance
gcloud compute instances add-tags YOUR_INSTANCE_NAME \
    --zone=YOUR_ZONE \
    --tags=allow-nodeport,argocd-server

# Verify tags were added
gcloud compute instances describe YOUR_INSTANCE_NAME \
    --zone=YOUR_ZONE \
    --format='get(tags.items[])'
```

Then update your firewall rule to use these tags:

```bash
gcloud compute firewall-rules update allow-argocd-31513 \
    --target-tags=allow-nodeport,argocd-server
```

### Step 6: Test NodePort Locally on GCP Instance

SSH into your GCP instance and test:

```bash
# SSH into instance
gcloud compute ssh YOUR_INSTANCE_NAME --zone=YOUR_ZONE

# Test if ArgoCD responds on the NodePort
curl -v http://localhost:31513

# Should show HTML response or redirect to HTTPS
```

If this works, the issue is **definitely firewall-related**.

### Step 7: Check if Using HTTP vs HTTPS

ArgoCD by default uses HTTPS. Try accessing with HTTPS:

```
https://34.171.44.90:31513/
```

**OR** expose HTTP port specifically:

```bash
# Check which port is which
kubectl get svc argocd-server -n argocd

# You might need to use the HTTPS NodePort instead
```

---

## Quick Fix Commands

### Option 1: Comprehensive Firewall Rule (Recommended)

```bash
# Allow all NodePorts from anywhere
gcloud compute firewall-rules create allow-nodeports-all \
    --allow tcp:30000-32767,udp:30000-32767 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow all Kubernetes NodePorts"

# Wait 30 seconds for rule to propagate
sleep 30

# Test access
curl -v http://34.171.44.90:31513
```

### Option 2: Specific Port Rule

```bash
# Allow only ArgoCD port
gcloud compute firewall-rules create allow-argocd \
    --allow tcp:31513 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow ArgoCD NodePort"
```

### Option 3: Use LoadBalancer Instead

If NodePort continues to have issues:

```bash
# Change service to LoadBalancer
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'

# Wait for external IP (takes 2-3 minutes)
kubectl get svc argocd-server -n argocd --watch

# Access via the EXTERNAL-IP shown
```

---

## Diagnostic Commands

### 1. Check if Firewall Rule Exists

```bash
gcloud compute firewall-rules list --filter="allowed[]:31513"
```

### 2. Test Port Connectivity

From your local machine:

```bash
# Test with netcat (install with: brew install netcat on Mac)
nc -zv 34.171.44.90 31513

# Test with telnet
telnet 34.171.44.90 31513

# Test with nmap (if installed)
nmap -p 31513 34.171.44.90
```

### 3. Check GCP Instance Firewall Status

```bash
# From within GCP instance
sudo iptables -L -n | grep 31513

# Check if port is listening
sudo netstat -tulpn | grep 31513
```

### 4. Check Kubernetes Service

```bash
# Get service details
kubectl describe svc argocd-server -n argocd

# Check endpoints
kubectl get endpoints argocd-server -n argocd
```

---

## Most Likely Solution

Based on your situation, here's the **most likely fix**:

```bash
# 1. Verify instance name and zone
gcloud compute instances list

# 2. Create firewall rule with NO target tags (applies to all instances)
gcloud compute firewall-rules create allow-argocd-nodeport \
    --allow tcp:31513 \
    --source-ranges 0.0.0.0/0 \
    --network default \
    --description "Allow ArgoCD access"

# 3. Wait 30 seconds
sleep 30

# 4. Test from your browser
# http://34.171.44.90:31513
```

**If this doesn't work**, add this:

```bash
# Update the rule to explicitly target your VPC network
gcloud compute firewall-rules update allow-argocd-nodeport \
    --network=default

# Or if using custom VPC
gcloud compute networks list  # Find your network name
gcloud compute firewall-rules update allow-argocd-nodeport \
    --network=YOUR_VPC_NETWORK
```

---

## Alternative: Use Port-Forward as a Solution

If you want to keep using port-forward (simpler for development):

### On GCP Instance:

```bash
# Run port-forward in background
nohup kubectl port-forward --address 0.0.0.0 service/argocd-server 80:80 -n argocd > /dev/null 2>&1 &

# Or use screen/tmux to keep it running
screen -dmS argocd kubectl port-forward --address 0.0.0.0 service/argocd-server 80:80 -n argocd
```

### Create Systemd Service (Persistent):

Create `/etc/systemd/system/argocd-port-forward.service`:

```ini
[Unit]
Description=ArgoCD Port Forward
After=network.target

[Service]
Type=simple
User=YOUR_USER
ExecStart=/usr/local/bin/kubectl port-forward --address 0.0.0.0 service/argocd-server 80:80 -n argocd
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable it:
```bash
sudo systemctl daemon-reload
sudo systemctl enable argocd-port-forward
sudo systemctl start argocd-port-forward
sudo systemctl status argocd-port-forward
```

Then access via: `http://34.171.44.90` (port 80)

---

## Security Note

If using `--source-ranges 0.0.0.0/0`, you're allowing access from anywhere. For production:

```bash
# Restrict to your IP only
MY_IP=$(curl -s ifconfig.me)
gcloud compute firewall-rules update allow-argocd-nodeport \
    --source-ranges ${MY_IP}/32
```

---

## Verification Checklist

- [ ] ArgoCD pods are running: `kubectl get pods -n argocd`
- [ ] Service is NodePort type: `kubectl get svc argocd-server -n argocd`
- [ ] Firewall rule exists: `gcloud compute firewall-rules list | grep argocd`
- [ ] Firewall rule allows port 31513
- [ ] Firewall rule has correct source ranges (0.0.0.0/0)
- [ ] Instance has correct network tags (if rule uses target tags)
- [ ] Port accessible locally on instance: `curl http://localhost:31513`
- [ ] Tried both HTTP and HTTPS
- [ ] Waited at least 30 seconds after creating firewall rule

---

## Still Not Working?

### Debug with VPC Flow Logs

```bash
# Enable VPC flow logs (if not already)
gcloud compute networks subnets update YOUR_SUBNET \
    --region=YOUR_REGION \
    --enable-flow-logs

# Check logs in Cloud Console
# Navigation: VPC Network → Firewall → Firewall Insights
```

### Check GCP Console

1. Go to **VPC Network → Firewall** in GCP Console
2. Look for your rule
3. Check "Logs" tab to see if traffic is being denied
4. View "Filter" to ensure your instance is covered

### Contact Information

If issue persists after trying all above:
1. Share output of: `kubectl get svc argocd-server -n argocd -o yaml`
2. Share output of: `gcloud compute firewall-rules list`
3. Share output of: `gcloud compute instances describe YOUR_INSTANCE --zone=YOUR_ZONE`
