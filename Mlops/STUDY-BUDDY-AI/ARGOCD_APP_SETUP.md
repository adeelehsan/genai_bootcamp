# ArgoCD Application Setup Guide

## Current Status

You have ArgoCD installed but **no applications created yet**.

```bash
kubectl get applications -n argocd
# Output: No resources found in argocd namespace.
```

This means ArgoCD doesn't know what to deploy. Let's fix that!

---

## Solution: Create ArgoCD Application

### Option 1: Create via YAML (Recommended)

#### Step 1: Create the Application YAML

The `argocd-application.yaml` file has been created with this configuration:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: study-buddy-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/adeelehsan/genai_bootcamp.git
    targetRevision: main
    path: Mlops/STUDY-BUDDY-AI/manifests
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

#### Step 2: Apply the Application

```bash
# SSH into your GCP instance
gcloud compute ssh instance-20251213-180737 --zone=YOUR_ZONE

# Apply the ArgoCD application
kubectl apply -f argocd-application.yaml

# Or apply from the repo
kubectl apply -f https://raw.githubusercontent.com/adeelehsan/genai_bootcamp/main/Mlops/STUDY-BUDDY-AI/argocd-application.yaml
```

#### Step 3: Verify Application Created

```bash
# List applications
kubectl get applications -n argocd

# Should show: study-buddy-app

# Get detailed info
kubectl describe application study-buddy-app -n argocd

# Check sync status
kubectl get application study-buddy-app -n argocd -o jsonpath='{.status.sync.status}'
```

---

### Option 2: Create via ArgoCD CLI

```bash
# Login to ArgoCD
argocd login 34.171.44.90 --grpc-web --insecure

# Create application
argocd app create study-buddy-app \
  --repo https://github.com/adeelehsan/genai_bootcamp.git \
  --path Mlops/STUDY-BUDDY-AI/manifests \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace default \
  --sync-policy automated \
  --auto-prune \
  --self-heal

# Verify
argocd app list

# Sync the application
argocd app sync study-buddy-app
```

---

### Option 3: Create via ArgoCD UI

1. **Access ArgoCD UI:**
   - Open: `http://34.171.44.90` or `https://34.171.44.90`
   - Login with username: `admin`
   - Password:
     ```bash
     kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" | base64 -d
     ```

2. **Click "+ NEW APP"**

3. **Fill in the form:**
   - **Application Name:** `study-buddy-app`
   - **Project:** `default`
   - **Sync Policy:** `Automatic`
   - **Repository URL:** `https://github.com/adeelehsan/genai_bootcamp.git`
   - **Revision:** `main`
   - **Path:** `Mlops/STUDY-BUDDY-AI/manifests`
   - **Cluster URL:** `https://kubernetes.default.svc`
   - **Namespace:** `default`

4. **Click "CREATE"**

5. **Click "SYNC"** to deploy

---

## Configuration Details

### Repository Information

| Field | Value |
|-------|-------|
| **Repo URL** | `https://github.com/adeelehsan/genai_bootcamp.git` |
| **Branch** | `main` |
| **Path** | `Mlops/STUDY-BUDDY-AI/manifests` |

### Deployment Target

| Field | Value |
|-------|-------|
| **Cluster** | `https://kubernetes.default.svc` (local cluster) |
| **Namespace** | `default` |

### Sync Policy

| Setting | Value | Description |
|---------|-------|-------------|
| **Automated** | `true` | Auto-sync on Git changes |
| **Prune** | `true` | Delete removed resources |
| **Self-Heal** | `true` | Fix manual changes |

---

## Verify Deployment

### Check Application Status

```bash
# Get application status
kubectl get application study-buddy-app -n argocd

# Expected output:
# NAME              SYNC STATUS   HEALTH STATUS
# study-buddy-app   Synced        Healthy
```

### Check Deployed Resources

```bash
# List all resources in default namespace
kubectl get all -n default

# Should show:
# - deployment/llmops-app
# - service/llmops-service
# - pods/llmops-app-xxxxx
```

### Check Application in ArgoCD UI

1. Open: `http://34.171.44.90`
2. You should see the `study-buddy-app` application
3. Click on it to see the resource tree

---

## Understanding ArgoCD Application Components

### What's in the Manifests Directory?

```bash
Mlops/STUDY-BUDDY-AI/manifests/
├── deployment.yaml       # Kubernetes Deployment
├── service.yaml          # Kubernetes Service
├── secrets-example.yaml  # Example secrets (not deployed)
└── README.md            # Documentation
```

### What ArgoCD Will Deploy

When you create the application, ArgoCD will:

1. ✅ Clone your GitHub repository
2. ✅ Read `Mlops/STUDY-BUDDY-AI/manifests/`
3. ✅ Apply `deployment.yaml` → Creates pods
4. ✅ Apply `service.yaml` → Creates NodePort service
5. ✅ Monitor for changes and auto-sync

---

## Sync Policies Explained

### Automated Sync

```yaml
syncPolicy:
  automated:
    prune: true      # Delete resources removed from Git
    selfHeal: true   # Revert manual kubectl changes
```

**With this enabled:**
- ✅ Jenkins pushes new image tag → ArgoCD auto-deploys
- ✅ Someone does `kubectl delete pod` → ArgoCD recreates it
- ✅ Git manifest updated → ArgoCD syncs automatically

### Manual Sync

```yaml
syncPolicy: {}  # No automated sync
```

**Requires manual sync:**
```bash
argocd app sync study-buddy-app
```

---

## Complete Setup Script

Run this on your GCP instance:

```bash
#!/bin/bash

set -e

echo "======================================"
echo "ArgoCD Application Setup"
echo "======================================"

# Variables
APP_NAME="study-buddy-app"
REPO_URL="https://github.com/adeelehsan/genai_bootcamp.git"
REPO_PATH="Mlops/STUDY-BUDDY-AI/manifests"
NAMESPACE="default"

echo "Creating ArgoCD application: $APP_NAME"

# Create application via kubectl
cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: $APP_NAME
  namespace: argocd
spec:
  project: default
  source:
    repoURL: $REPO_URL
    targetRevision: main
    path: $REPO_PATH
  destination:
    server: https://kubernetes.default.svc
    namespace: $NAMESPACE
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
    - CreateNamespace=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
EOF

echo ""
echo "Waiting for application to be created..."
sleep 5

# Check application status
echo ""
echo "Application Status:"
kubectl get application $APP_NAME -n argocd

echo ""
echo "Syncing application..."
kubectl patch application $APP_NAME -n argocd \
  --type merge \
  -p '{"operation":{"initiatedBy":{"username":"admin"},"sync":{"revision":"main"}}}'

echo ""
echo "Waiting for sync to complete..."
sleep 10

# Show final status
echo ""
echo "======================================"
echo "Final Status:"
echo "======================================"
kubectl get application $APP_NAME -n argocd

echo ""
echo "Deployed Resources:"
kubectl get all -n $NAMESPACE

echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo "View in ArgoCD UI: http://34.171.44.90"
echo "Application Name: $APP_NAME"
echo "======================================"
```

Save as `setup-argocd-app.sh` and run:

```bash
chmod +x setup-argocd-app.sh
./setup-argocd-app.sh
```

---

## Troubleshooting

### Issue 1: "repository not accessible"

**Cause:** ArgoCD can't access your GitHub repo (if private)

**Fix:** Add GitHub credentials to ArgoCD

```bash
# For public repos (no credentials needed)
# Your repo should work as-is

# For private repos:
argocd repo add https://github.com/adeelehsan/genai_bootcamp.git \
  --username YOUR_USERNAME \
  --password YOUR_GITHUB_TOKEN
```

### Issue 2: Application status shows "Unknown"

**Cause:** ArgoCD hasn't synced yet

**Fix:**
```bash
# Manually trigger sync
argocd app sync study-buddy-app

# Or via kubectl
kubectl patch application study-buddy-app -n argocd \
  --type merge \
  -p '{"operation":{"sync":{}}}'
```

### Issue 3: "path does not exist"

**Cause:** Wrong path in application config

**Fix:** Verify the path exists in your repo:
```bash
# Check on GitHub:
# https://github.com/adeelehsan/genai_bootcamp/tree/main/Mlops/STUDY-BUDDY-AI/manifests

# Should contain:
# - deployment.yaml
# - service.yaml
```

### Issue 4: Secrets not found

**Cause:** Kubernetes secrets not created

**Fix:** Create secrets before syncing:
```bash
kubectl create secret generic groq-api-secret \
  --from-literal=GROQ_API_KEY=your_key \
  -n default

kubectl create secret generic openai-api-secret \
  --from-literal=OPENAI_API_KEY=your_key \
  -n default
```

---

## Jenkins Integration

Once the ArgoCD application is created, update your Jenkinsfile to use the correct app name:

```groovy
# Line 97 in Jenkinsfile
argocd app sync study-buddy-app
```

---

## Monitoring

### Check Application Health

```bash
# Via kubectl
kubectl get application study-buddy-app -n argocd -o jsonpath='{.status.health.status}'

# Via ArgoCD CLI
argocd app get study-buddy-app
```

### Check Sync Status

```bash
# Via kubectl
kubectl get application study-buddy-app -n argocd -o jsonpath='{.status.sync.status}'

# Via ArgoCD CLI
argocd app list
```

### View Application in UI

1. Open: `http://34.171.44.90`
2. Login with admin credentials
3. Click on `study-buddy-app`
4. See resource tree and sync status

---

## Next Steps

1. ✅ Create the ArgoCD application (use Option 1)
2. ✅ Verify it's created: `kubectl get applications -n argocd`
3. ✅ Check sync status
4. ✅ View in ArgoCD UI
5. ✅ Test Jenkins pipeline with the correct app name

---

## Summary

**What you need to do:**

```bash
# 1. Apply the ArgoCD application
kubectl apply -f argocd-application.yaml

# 2. Verify it's created
kubectl get applications -n argocd

# 3. Check sync status
argocd app get study-buddy-app

# 4. Access UI
# http://34.171.44.90
```

Now your Jenkins pipeline will be able to sync the `study-buddy-app` application! 🚀
