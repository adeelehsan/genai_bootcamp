# Kubernetes Manifests

This directory contains Kubernetes deployment manifests for Study Buddy AI.

## Files

- **deployment.yaml** - Deployment configuration with 2 replicas
- **service.yaml** - NodePort service exposing the application
- **secrets-example.yaml** - Example secret configuration (DO NOT commit actual secrets)

## Prerequisites

1. Kubernetes cluster (local or cloud)
2. kubectl configured
3. API keys for Groq and/or OpenAI

## Deployment Steps

### 1. Create Secrets

**Option A: From Literal Values (Recommended)**

```bash
# Create Groq API secret
kubectl create secret generic groq-api-secret \
  --from-literal=GROQ_API_KEY=your_groq_api_key_here

# Create OpenAI API secret (if using OpenAI models)
kubectl create secret generic openai-api-secret \
  --from-literal=OPENAI_API_KEY=your_openai_api_key_here
```

**Option B: From Base64 Encoded Values**

```bash
# Encode your API keys
echo -n 'your_groq_api_key' | base64
echo -n 'your_openai_api_key' | base64

# Copy the output and update secrets-example.yaml
# Then apply:
kubectl apply -f manifests/secrets-example.yaml
```

### 2. Verify Secrets

```bash
# List secrets
kubectl get secrets

# Check secret details (encoded)
kubectl describe secret groq-api-secret
kubectl describe secret openai-api-secret
```

### 3. Deploy Application

```bash
# Apply deployment
kubectl apply -f manifests/deployment.yaml

# Apply service
kubectl apply -f manifests/service.yaml
```

### 4. Verify Deployment

```bash
# Check deployment status
kubectl get deployments

# Check pods
kubectl get pods

# Check service
kubectl get services

# View logs
kubectl logs -l app=llmops-app
```

### 5. Access Application

**For NodePort Service:**

```bash
# Get NodePort
kubectl get service llmops-service

# Access application at:
# http://<node-ip>:<node-port>
```

**For Port Forwarding (local testing):**

```bash
kubectl port-forward service/llmops-service 8501:80

# Access at: http://localhost:8501
```

## Environment Variables

The deployment expects these secrets:

- **GROQ_API_KEY** - Required for Groq models (LLaMA, Mixtral)
- **OPENAI_API_KEY** - Required for OpenAI models (GPT-4, GPT-3.5)

**Note:** You only need to create secrets for the providers you plan to use.

## Updating Secrets

```bash
# Delete existing secret
kubectl delete secret groq-api-secret

# Create new secret with updated key
kubectl create secret generic groq-api-secret \
  --from-literal=GROQ_API_KEY=new_api_key_here

# Restart pods to use new secret
kubectl rollout restart deployment llmops-app
```

## Scaling

```bash
# Scale up
kubectl scale deployment llmops-app --replicas=5

# Scale down
kubectl scale deployment llmops-app --replicas=1
```

## Cleanup

```bash
# Delete all resources
kubectl delete -f manifests/deployment.yaml
kubectl delete -f manifests/service.yaml
kubectl delete secret groq-api-secret
kubectl delete secret openai-api-secret
```

## Security Best Practices

1. **Never commit secrets to git** - Use `.gitignore` for secret files
2. **Use RBAC** - Restrict access to secrets
3. **Rotate keys regularly** - Update secrets periodically
4. **Use external secret management** - Consider using:
   - External Secrets Operator
   - HashiCorp Vault
   - AWS Secrets Manager
   - Azure Key Vault
   - Google Secret Manager

## Troubleshooting

### Pod fails to start

```bash
# Check pod status
kubectl describe pod <pod-name>

# Check logs
kubectl logs <pod-name>
```

### Secret not found error

```bash
# Verify secrets exist
kubectl get secrets | grep api-secret

# Recreate missing secrets
kubectl create secret generic groq-api-secret --from-literal=GROQ_API_KEY=your_key
```

### Application can't connect to models

1. Verify secrets are correctly configured
2. Check environment variables in pod:
   ```bash
   kubectl exec <pod-name> -- env | grep API_KEY
   ```
3. Check application logs for API errors
