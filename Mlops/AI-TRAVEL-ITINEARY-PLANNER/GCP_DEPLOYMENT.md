# AI Travel Itinerary Planner - GCP Deployment Guide

This guide walks you through deploying the AI Travel Itinerary Planner on Google Cloud Platform (GCP) using a Compute Engine E2 instance.

## Prerequisites

- GCP account with billing enabled
- Basic knowledge of SSH and Linux commands
- Your `GROQ_API_KEY` ready

## Architecture

- **Instance Type**: E2-micro (free tier eligible)
- **OS**: Ubuntu 22.04 LTS
- **Application Port**: 8501 (Streamlit default)
- **Container**: Docker
- **Access**: Public IP with firewall rule

---

## Step 1: Create GCP Compute Engine Instance

### 1.1 Go to VM Instances
1. Navigate to **Compute Engine** > **VM Instances**
2. Click **Create Instance**

### 1.2 Configure Instance
```
Name: travel-planner-app
Region: us-central1 (or your preferred region)
Zone: us-central1-a

Machine configuration:
  Series: E2
  Machine type: e2-micro (2 vCPU, 1 GB memory) - Free tier eligible

Boot disk:
  Operating System: Ubuntu
  Version: Ubuntu 22.04 LTS
  Boot disk type: Standard persistent disk
  Size: 10 GB

Firewall:
  ☑️ Allow HTTP traffic
  ☑️ Allow HTTPS traffic
```

### 1.3 Create the Instance
- Click **Create**
- Wait for the instance to start (green checkmark)

---

## Step 2: Configure Firewall Rule for Port 8501

### 2.1 Create Firewall Rule
1. Go to **VPC Network** > **Firewall**
2. Click **Create Firewall Rule**

### 2.2 Firewall Configuration
```
Name: allow-streamlit-8501
Description: Allow Streamlit traffic on port 8501

Network: default

Priority: 1000

Direction of traffic: Ingress

Action on match: Allow

Targets: All instances in the network

Source IP ranges: 0.0.0.0/0

Protocols and ports:
  ☑️ Specified protocols and ports
  TCP: 8501
```

3. Click **Create**

---

## Step 3: Connect to Your Instance

### 3.1 SSH into Instance
```bash
# From GCP Console, click "SSH" button next to your instance
# Or use gcloud CLI:
gcloud compute ssh travel-planner-app --zone=us-central1-a
```

---

## Step 4: Install Docker on the Instance

### 4.1 Update System
```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 4.2 Install Docker
```bash
# Install dependencies
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add current user to docker group (to run docker without sudo)
sudo usermod -aG docker $USER

# Apply group changes
newgrp docker
```

### 4.3 Verify Docker Installation
```bash
docker --version
docker run hello-world
```

---

## Step 5: Deploy the Application

### 5.1 Clone the Repository
```bash
cd ~
git clone <your-repo-url>
cd AI-TRAVEL-ITINEARY-PLANNER
```

**Or upload files manually:**
```bash
# From your local machine
gcloud compute scp --recurse /path/to/AI-TRAVEL-ITINEARY-PLANNER travel-planner-app:~/ --zone=us-central1-a
```

### 5.2 Create .env File
```bash
nano .env
```

Add your environment variables:
```
GROQ_API_KEY=your_actual_groq_api_key_here
```

Save and exit (Ctrl+X, then Y, then Enter)

### 5.3 Make Deploy Script Executable
```bash
chmod +x deploy.sh
```

### 5.4 Run Deployment
```bash
./deploy.sh
```

---

## Step 6: Access Your Application

### 6.1 Get Your External IP
```bash
# From GCP Console: VM Instances > External IP column
# Or via command:
gcloud compute instances describe travel-planner-app --zone=us-central1-a --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

### 6.2 Open in Browser
```
http://YOUR_EXTERNAL_IP:8501
```

Example: `http://35.192.146.75:8501`

---

## Step 7: Verify Deployment

### 7.1 Check Container Status
```bash
docker ps
```

Expected output:
```
CONTAINER ID   IMAGE            STATUS        PORTS                    NAMES
xxxxx          travel-planner   Up 2 minutes  0.0.0.0:8501->8501/tcp   travel-planner-app
```

### 7.2 Check Application Logs
```bash
docker logs -f travel-planner-app
```

You should see:
```
You can now view your Streamlit app in your browser.

Network URL: http://0.0.0.0:8501
External URL: http://YOUR_IP:8501
```

---

## Useful Commands

### Container Management
```bash
# View running containers
docker ps

# View all containers (including stopped)
docker ps -a

# Stop the application
docker stop travel-planner-app

# Start the application
docker start travel-planner-app

# Restart the application
docker restart travel-planner-app

# Remove container
docker rm travel-planner-app

# View logs
docker logs -f travel-planner-app
```

### Redeploy After Code Changes
```bash
# Pull latest changes
git pull

# Redeploy
./deploy.sh
```

### System Monitoring
```bash
# Check disk space
df -h

# Check memory usage
free -h

# Check Docker disk usage
docker system df

# Clean up Docker resources
docker system prune -a
```

---

## Cost Optimization

### Free Tier Limits (as of 2024)
- **E2-micro instance**: 1 instance free per month in us-central1, us-west1, or us-east1
- **Storage**: 30 GB standard persistent disk free
- **Egress**: 1 GB network egress free per month

### Tips
1. Use E2-micro in free tier regions
2. Stop instance when not in use (you'll still pay for disk storage)
3. Set up budget alerts in GCP Console
4. Monitor usage in Billing dashboard

---

## Troubleshooting

### Application Not Accessible

**Check firewall rule:**
```bash
gcloud compute firewall-rules list --filter="name=allow-streamlit-8501"
```

**Check if container is running:**
```bash
docker ps
```

**Check container logs for errors:**
```bash
docker logs travel-planner-app
```

### Port Already in Use

**Find process using port 8501:**
```bash
sudo lsof -i :8501
```

**Kill the process:**
```bash
sudo kill -9 <PID>
```

### Out of Memory

**Check memory:**
```bash
free -h
docker stats
```

**Solution**: Upgrade to larger instance (e2-small or e2-medium)

### Docker Permission Denied

```bash
sudo usermod -aG docker $USER
newgrp docker
```

---

## Security Best Practices

### 1. Restrict Firewall Access
Instead of `0.0.0.0/0`, use specific IP ranges:
```bash
# Update firewall rule
gcloud compute firewall-rules update allow-streamlit-8501 \
  --source-ranges="YOUR_IP/32"
```

### 2. Enable HTTPS (Optional)

**Install Nginx:**
```bash
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

**Configure Nginx as reverse proxy:**
```bash
sudo nano /etc/nginx/sites-available/travel-planner
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

**Enable site and get SSL:**
```bash
sudo ln -s /etc/nginx/sites-available/travel-planner /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo certbot --nginx -d your-domain.com
```

### 3. Use Secret Manager (Production)
Instead of .env files, use GCP Secret Manager:
```bash
# Create secret
echo -n "your-groq-api-key" | gcloud secrets create groq-api-key --data-file=-

# Grant access to compute service account
gcloud secrets add-iam-policy-binding groq-api-key \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

---

## Maintenance

### Auto-restart on Reboot
The `--restart unless-stopped` flag ensures the container restarts automatically after system reboot.

### Update Application
```bash
cd ~/AI-TRAVEL-ITINEARY-PLANNER
git pull
./deploy.sh
```

### Backup
```bash
# Backup configuration
tar -czf travel-planner-backup.tar.gz .env app.py src/

# Download to local machine
gcloud compute scp travel-planner-app:~/travel-planner-backup.tar.gz ./ --zone=us-central1-a
```

---

## Support

For issues or questions:
1. Check application logs: `docker logs -f travel-planner-app`
2. Check GCP logs: Cloud Logging in GCP Console
3. Verify firewall rules: VPC Network > Firewall
4. Test locally first: `./deploy.sh` on your machine

---

## Clean Up (Delete Everything)

**To avoid charges:**
```bash
# Delete VM instance
gcloud compute instances delete travel-planner-app --zone=us-central1-a

# Delete firewall rule
gcloud compute firewall-rules delete allow-streamlit-8501

# Delete disk (if not auto-deleted)
gcloud compute disks list
gcloud compute disks delete DISK_NAME --zone=us-central1-a
```

---

**Deployment Complete!** Your AI Travel Itinerary Planner is now accessible at `http://YOUR_EXTERNAL_IP:8501` 🎉
