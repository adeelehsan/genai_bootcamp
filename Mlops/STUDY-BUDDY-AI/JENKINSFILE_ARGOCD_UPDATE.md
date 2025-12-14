# Jenkinsfile ArgoCD Stage Update Guide

## What Changed

With your LoadBalancer setup, the ArgoCD access method has changed:

### Before (NodePort)
```
argocd login 34.45.193.5:31704
```

### After (LoadBalancer)
```
argocd login 34.171.44.90 --grpc-web
```

---

## Required Updates

### 1. Update ArgoCD Server URL

Replace the old IP/port with your current setup:

**If using Nginx Reverse Proxy on standard ports:**
```groovy
argocd login 34.171.44.90 --username admin --password $ARGOCD_PASSWORD --insecure --grpc-web
```

**If using HTTPS NodePort (30529):**
```groovy
argocd login 34.171.44.90:30529 --username admin --password $ARGOCD_PASSWORD --insecure
```

**If using HTTP NodePort (31513):**
```groovy
argocd login 34.171.44.90:31513 --username admin --password $ARGOCD_PASSWORD --insecure --plaintext --grpc-web
```

### 2. Add `--grpc-web` Flag

When using LoadBalancer/Nginx, ArgoCD CLI needs the `--grpc-web` flag to communicate properly through HTTP/HTTPS.

**Why?**
- NodePort → Direct gRPC connection ✅
- LoadBalancer/Nginx → HTTP/HTTPS, needs `--grpc-web` wrapper ✅

### 3. Update App Name (If Different)

Replace `study` with your actual ArgoCD application name:

```bash
# List your ArgoCD apps
kubectl get applications -n argocd

# Update in Jenkinsfile
argocd app sync YOUR_APP_NAME
```

---

## Complete Updated Stage

Here's the full updated stage:

```groovy
stage('Apply Kubernetes & Sync App with ArgoCD') {
    steps {
        script {
            kubeconfig(credentialsId: 'kubeconfig', serverUrl: 'https://192.168.49.2:8443') {
                sh '''
                # Get ArgoCD admin password
                ARGOCD_PASSWORD=$(kubectl get secret -n argocd argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)

                # Login to ArgoCD via LoadBalancer
                echo "Logging into ArgoCD..."
                argocd login 34.171.44.90 \
                    --username admin \
                    --password $ARGOCD_PASSWORD \
                    --insecure \
                    --grpc-web

                # Verify login
                argocd account get-user-info

                # List applications
                echo "Available ArgoCD applications:"
                argocd app list

                # Sync application
                echo "Syncing application..."
                argocd app sync study-buddy-app --force --prune

                # Wait for sync to complete
                argocd app wait study-buddy-app --health --timeout 300

                # Show application status
                argocd app get study-buddy-app
                '''
            }
        }
    }
}
```

---

## Environment Variables Approach (Recommended)

Make it configurable:

```groovy
environment {
    DOCKER_HUB_REPO = "dataguru97/studybuddy"
    DOCKER_HUB_CREDENTIALS_ID = "dockerhub-token"
    IMAGE_TAG = "v${BUILD_NUMBER}"
    PROJECT_DIR = 'Mlops/STUDY-BUDDY-AI'
    GITHUB_REPO_URL = 'https://github.com/adeelehsan/genai_bootcamp.git'

    // ArgoCD Configuration
    ARGOCD_SERVER = '34.171.44.90'          // Your LoadBalancer IP
    ARGOCD_PORT = ''                        // Leave empty for standard ports (80/443)
    ARGOCD_APP_NAME = 'study-buddy-app'     // Your ArgoCD application name
    ARGOCD_USE_GRPC_WEB = 'true'           // Set to true for LoadBalancer/Nginx
}
```

Then update the stage:

```groovy
stage('Apply Kubernetes & Sync App with ArgoCD') {
    steps {
        script {
            kubeconfig(credentialsId: 'kubeconfig', serverUrl: 'https://192.168.49.2:8443') {
                sh '''
                # Get ArgoCD admin password
                ARGOCD_PASSWORD=$(kubectl get secret -n argocd argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)

                # Build ArgoCD server URL
                ARGOCD_URL="${ARGOCD_SERVER}"
                if [ -n "${ARGOCD_PORT}" ]; then
                    ARGOCD_URL="${ARGOCD_SERVER}:${ARGOCD_PORT}"
                fi

                # Build login command
                LOGIN_CMD="argocd login ${ARGOCD_URL} --username admin --password ${ARGOCD_PASSWORD} --insecure"

                # Add grpc-web if needed
                if [ "${ARGOCD_USE_GRPC_WEB}" = "true" ]; then
                    LOGIN_CMD="${LOGIN_CMD} --grpc-web"
                fi

                # Login
                echo "Logging into ArgoCD at ${ARGOCD_URL}..."
                eval $LOGIN_CMD

                # Sync application
                echo "Syncing ArgoCD application: ${ARGOCD_APP_NAME}"
                argocd app sync ${ARGOCD_APP_NAME} --force --prune

                # Wait for sync
                argocd app wait ${ARGOCD_APP_NAME} --health --timeout 300
                '''
            }
        }
    }
}
```

---

## Troubleshooting

### Issue 1: "context deadline exceeded"

**Cause**: ArgoCD server not accessible or wrong URL

**Fix**:
```bash
# Test ArgoCD accessibility
curl -k https://34.171.44.90

# Try with --grpc-web flag
argocd login 34.171.44.90 --grpc-web --insecure
```

### Issue 2: "rpc error: code = Unavailable"

**Cause**: gRPC communication blocked by proxy

**Fix**: Add `--grpc-web` flag:
```bash
argocd login 34.171.44.90 --grpc-web --insecure
```

### Issue 3: "application not found"

**Cause**: Wrong application name

**Fix**:
```bash
# List all apps
kubectl get applications -n argocd

# Or via ArgoCD CLI
argocd app list
```

### Issue 4: "Unauthorized"

**Cause**: Password incorrect or expired

**Fix**:
```bash
# Get current password
kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath="{.data.password}" | base64 -d

# Or reset password
kubectl delete secret argocd-initial-admin-secret -n argocd
kubectl rollout restart deployment argocd-server -n argocd
```

---

## Verification Commands

### Test ArgoCD Login from Jenkins

```bash
# SSH into Jenkins server
# Then test ArgoCD login

# Get password
ARGOCD_PASSWORD=$(kubectl get secret -n argocd argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)

# Test login (with LoadBalancer)
argocd login 34.171.44.90 \
    --username admin \
    --password $ARGOCD_PASSWORD \
    --insecure \
    --grpc-web

# Should see: "Logged in successfully"

# List apps
argocd app list

# Test sync
argocd app sync YOUR_APP_NAME --dry-run
```

---

## Different LoadBalancer Scenarios

### Scenario 1: Nginx Reverse Proxy (Standard Ports)

```groovy
# HTTP (port 80)
argocd login 34.171.44.90 \
    --username admin \
    --password $ARGOCD_PASSWORD \
    --insecure \
    --plaintext \
    --grpc-web

# HTTPS (port 443)
argocd login 34.171.44.90 \
    --username admin \
    --password $ARGOCD_PASSWORD \
    --insecure \
    --grpc-web
```

### Scenario 2: MetalLB + Port Forward

```groovy
# Still uses NodePorts
argocd login 34.171.44.90:31513 \
    --username admin \
    --password $ARGOCD_PASSWORD \
    --insecure \
    --plaintext \
    --grpc-web
```

### Scenario 3: GCP Load Balancer

```groovy
# Use Load Balancer IP
argocd login <LOAD_BALANCER_IP> \
    --username admin \
    --password $ARGOCD_PASSWORD \
    --insecure \
    --grpc-web
```

---

## Best Practices

### 1. Use ArgoCD in Insecure Mode (for Internal CI/CD)

```groovy
argocd login $ARGOCD_SERVER \
    --username admin \
    --password $ARGOCD_PASSWORD \
    --insecure
```

### 2. Add Timeout for Sync

```groovy
argocd app sync $APP_NAME --timeout 300
```

### 3. Force Sync on Update

```groovy
argocd app sync $APP_NAME --force --prune
```

### 4. Check Health After Sync

```groovy
argocd app wait $APP_NAME --health --timeout 300
```

### 5. Get Detailed Status

```groovy
argocd app get $APP_NAME
```

---

## Complete Example with Error Handling

```groovy
stage('Apply Kubernetes & Sync App with ArgoCD') {
    steps {
        script {
            kubeconfig(credentialsId: 'kubeconfig', serverUrl: 'https://192.168.49.2:8443') {
                sh '''
                set -e

                echo "======================================"
                echo "ArgoCD Deployment Stage"
                echo "======================================"

                # Get ArgoCD admin password
                echo "Getting ArgoCD admin password..."
                ARGOCD_PASSWORD=$(kubectl get secret -n argocd argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)

                if [ -z "$ARGOCD_PASSWORD" ]; then
                    echo "ERROR: Failed to get ArgoCD password"
                    exit 1
                fi

                # Login to ArgoCD
                echo "Logging into ArgoCD at 34.171.44.90..."
                if argocd login 34.171.44.90 \
                    --username admin \
                    --password $ARGOCD_PASSWORD \
                    --insecure \
                    --grpc-web; then
                    echo "✅ Login successful"
                else
                    echo "❌ Login failed"
                    exit 1
                fi

                # Verify login
                echo "Verifying login..."
                argocd account get-user-info

                # List applications
                echo "Available ArgoCD applications:"
                argocd app list

                # Sync application
                echo "Syncing application: study-buddy-app"
                if argocd app sync study-buddy-app --force --prune --timeout 300; then
                    echo "✅ Sync successful"
                else
                    echo "❌ Sync failed"
                    argocd app get study-buddy-app
                    exit 1
                fi

                # Wait for application to be healthy
                echo "Waiting for application to be healthy..."
                if argocd app wait study-buddy-app --health --timeout 300; then
                    echo "✅ Application is healthy"
                else
                    echo "⚠️  Application health check timeout"
                    argocd app get study-buddy-app
                fi

                # Show final status
                echo "Final application status:"
                argocd app get study-buddy-app

                echo "======================================"
                echo "Deployment Complete!"
                echo "======================================"
                '''
            }
        }
    }
}
```

---

## Summary of Changes

| Item | Old Value | New Value |
|------|-----------|-----------|
| **Server** | `34.45.193.5:31704` | `34.171.44.90` |
| **Port** | `:31704` | None (standard 80/443) |
| **Flag** | None | `--grpc-web` |
| **App Name** | `study` | `study-buddy-app` (verify yours) |

---

## Quick Reference

**Minimal update:**
```groovy
argocd login 34.171.44.90 --username admin --password $ARGOCD_PASSWORD --insecure --grpc-web
argocd app sync study-buddy-app
```

**Full update with verification:**
```groovy
argocd login 34.171.44.90 --username admin --password $ARGOCD_PASSWORD --insecure --grpc-web
argocd app list
argocd app sync study-buddy-app --force --prune
argocd app wait study-buddy-app --health --timeout 300
argocd app get study-buddy-app
```
