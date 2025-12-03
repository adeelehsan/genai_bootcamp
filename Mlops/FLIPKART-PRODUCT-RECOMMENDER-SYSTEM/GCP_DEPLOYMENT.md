# Flipkart Product Recommender - GCP E2 Deployment Guide

## 🎯 **Goal**
Deploy the Flipkart app on GCP E2 instance (free tier) and make it accessible to others via public IP without port forwarding.

---

## 📋 **Prerequisites**

1. **GCP Account** with free tier access
2. **GCP Project** created
3. **gcloud CLI** installed (optional, can use console)

---

## 🚀 **Step-by-Step Deployment**

### **Step 1: Create GCP E2 Instance (Free Tier)**

#### **Option A: Via GCP Console (Recommended)**

1. Go to **Compute Engine** → **VM instances**
2. Click **Create Instance**
3. Configure:
   - **Name**: `flipkart-recommender`
   - **Region**: `us-central1` (or your closest free tier region)
   - **Zone**: Any (e.g., `us-central1-a`)
   - **Machine type**: `e2-micro` (free tier eligible)
   - **Boot disk**:
     - OS: **Ubuntu 22.04 LTS**
     - Size: **30 GB** (free tier limit)
   - **Firewall**:
     - ✅ Allow HTTP traffic
     - ✅ Allow HTTPS traffic
4. Click **Create**

#### **Option B: Via gcloud CLI**

```bash
gcloud compute instances create flipkart-recommender \
    --zone=us-central1-a \
    --machine-type=e2-micro \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=30GB \
    --tags=http-server,https-server
```

---

### **Step 2: Configure Firewall Rule for Port 5000**

Your app runs on port **5000**, so we need to allow traffic on that port.

#### **Via GCP Console:**

1. Go to **VPC Network** → **Firewall**
2. Click **Create Firewall Rule**
3. Configure:
   - **Name**: `allow-flask-5000`
   - **Direction**: Ingress
   - **Targets**: Specified target tags
   - **Target tags**: `http-server`
   - **Source IP ranges**: `0.0.0.0/0` (allow from anywhere)
   - **Protocols and ports**:
     - ✅ TCP: `5000`
4. Click **Create**

#### **Via gcloud CLI:**

```bash
gcloud compute firewall-rules create allow-flask-5000 \
    --allow tcp:5000 \
    --source-ranges 0.0.0.0/0 \
    --target-tags http-server \
    --description "Allow Flask app on port 5000"
```

---

### **Step 3: SSH into Your Instance**

#### **Via Console:**
- Go to VM instances → Click **SSH** button next to your instance

#### **Via gcloud CLI:**
```bash
gcloud compute ssh flipkart-recommender --zone=us-central1-a
```

---

### **Step 4: Install Dependencies on GCP Instance**

Once SSH'd into the instance, run:

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group (avoid sudo)
sudo usermod -aG docker $USER

# Install git
sudo apt-get install -y git

# Log out and log back in for docker group to take effect
exit
```

**SSH back in:**
```bash
gcloud compute ssh flipkart-recommender --zone=us-central1-a
```

Verify Docker:
```bash
docker --version
```

---

### **Step 5: Clone Your Repository**

```bash
# Clone your repo
git clone https://github.com/adeelehsan/genai_bootcamp.git
cd genai_bootcamp/Mlops/FLIPKART-PRODUCT-RECOMMENDER-SYSTEM/
```

---

### **Step 6: Create Environment Variables**

```bash
# Create .env file with your API keys
cat > .env << 'EOF'
GROQ_API_KEY=<Your API KEY>
HUGGINGFACEHUB_API_TOKEN="Your HF TOKEN"
EOF
```

---

### **Step 7: Build and Run with Docker**

```bash
# Build Docker image
docker build -t flipkart-recommender .

# Run container (detached mode, auto-restart)
docker run -d \
  --name flipkart-app \
  --restart unless-stopped \
  -p 5000:5000 \
  --env-file .env \
  flipkart-recommender
```

**Check if running:**
```bash
docker ps
docker logs flipkart-app
```

---

### **Step 8: Get Your Public IP**

#### **Via Console:**
- Go to **VM instances** → Find your instance → Copy **External IP**

#### **Via CLI on the instance:**
```bash
curl ifconfig.me
```

#### **Via gcloud CLI (from local):**
```bash
gcloud compute instances describe flipkart-recommender \
    --zone=us-central1-a \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

---

### **Step 9: Access Your App**

Open in browser:
```
http://<YOUR-EXTERNAL-IP>:5000
```

**Example:**
```
http://34.123.45.67:5000
```

**Share this URL with others!** ✅

---

## 🔧 **Alternative: Remove Port from URL (Optional)**

If you want a cleaner URL without `:5000`, use **Nginx as reverse proxy**:

### **Install Nginx:**

```bash
# On GCP instance
sudo apt-get install -y nginx
```

### **Configure Nginx:**

```bash
sudo tee /etc/nginx/sites-available/flipkart << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/flipkart /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

Now access via:
```
http://<YOUR-EXTERNAL-IP>
```
(No port needed!)

---

## 🛠️ **Useful Commands**

### **Check App Logs:**
```bash
docker logs -f flipkart-app
```

### **Restart App:**
```bash
docker restart flipkart-app
```

### **Stop App:**
```bash
docker stop flipkart-app
```

### **Update App (after code changes):**
```bash
cd ~/genai_bootcamp/Mlops/FLIPKART-PRODUCT-RECOMMENDER-SYSTEM/
git pull
docker stop flipkart-app
docker rm flipkart-app
docker build -t flipkart-recommender .
docker run -d --name flipkart-app --restart unless-stopped -p 5000:5000 --env-file .env flipkart-recommender
```

---

## 💰 **Free Tier Limits**

- **e2-micro instance**: 1 free per month (US regions only)
- **30 GB standard persistent disk**
- **1 GB network egress per month** (to certain regions)

**Your app will keep running 24/7 within free tier!**

---

## 🔒 **Security Best Practices**

1. **Restrict Firewall** (Optional):
   - Instead of `0.0.0.0/0`, use specific IP ranges if you know your users' IPs

2. **Use HTTPS** (Recommended for production):
   - Get a domain name
   - Use Let's Encrypt for free SSL certificate
   - Configure Nginx with SSL

3. **Environment Variables**:
   - Never commit `.env` to git (already in `.gitignore`)

---

## 📊 **Monitor Your App**

Your app has Prometheus metrics at:
```
http://<YOUR-IP>:5000/metrics
```

You can set up Grafana for visualization (already have configs in the project).

---

## ❓ **Troubleshooting**

### **App not accessible:**
```bash
# Check if Docker container is running
docker ps

# Check firewall
gcloud compute firewall-rules list | grep 5000

# Check app logs
docker logs flipkart-app
```

### **Instance stopped:**
- GCP may stop instances after inactivity on free tier
- Start it from console or CLI:
```bash
gcloud compute instances start flipkart-recommender --zone=us-central1-a
```

### **Port 5000 blocked:**
- Verify firewall rule exists
- Check instance network tags include `http-server`

---

## 🎉 **You're Done!**

Your Flipkart Product Recommender is now:
- ✅ Running 24/7 on GCP
- ✅ Accessible via public IP
- ✅ Free (within tier limits)
- ✅ Auto-restarts on crashes
- ✅ Sharable with others

**Share your URL:** `http://<YOUR-EXTERNAL-IP>:5000`
