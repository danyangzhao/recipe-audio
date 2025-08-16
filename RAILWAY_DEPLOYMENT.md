# Railway Deployment Guide

## 🚀 Deploying to Railway

### Step 1: Connect Your GitHub Repository

1. Go to [Railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your `recipe-audio` repository
5. Railway will automatically detect it's a Python app

### Step 2: Set Environment Variables

In your Railway project dashboard:

1. Go to the **Variables** tab
2. Add the following environment variables:

```env
OPENAI_API_KEY=your_openai_api_key_here
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_S3_BUCKET=your_s3_bucket_name
DATABASE_URL=postgresql://...  # Railway will auto-generate this
```

### Step 3: Configure the Build

Railway will automatically:
- Detect Python requirements.txt
- Install dependencies
- Use the gunicorn configuration
- Start the app on the provided PORT

### Step 4: Deploy

1. Railway will automatically deploy when you push to your main branch
2. Or click "Deploy" in the Railway dashboard
3. Wait for the build to complete

## 🔧 Configuration Files

### railway.json
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn app:app --config gunicorn_config.py",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### gunicorn_config.py
```python
import os

# Get the PORT from environment variable
port = os.getenv('PORT', '8000')

# Bind to 0.0.0.0:$PORT
bind = f"0.0.0.0:{port}"

# Railway-optimized configuration
workers = 1
threads = 2
worker_class = "gthread"
timeout = 60
keepalive = 2

# Memory management
max_requests = 25
max_requests_jitter = 5
worker_tmp_dir = "/dev/shm"
preload_app = True

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "warning"
```

## 🐛 Troubleshooting

### Common Issues

**1. "No OpenAI API key found"**
- Solution: Add `OPENAI_API_KEY` to Railway environment variables
- The app will show a helpful error message on the homepage

**2. "Module not found"**
- Solution: All dependencies are in requirements.txt
- Railway will install them automatically

**3. "Database connection failed"**
- Solution: Railway auto-generates `DATABASE_URL`
- Check that it's set in environment variables

**4. "Port binding error"**
- Solution: Railway sets the `PORT` environment variable
- The app automatically uses it

### Health Check

Visit `/health` to check if your app is running:
```json
{
  "status": "healthy",
  "openai_configured": true,
  "database_configured": true
}
```

### Logs

Check Railway logs in the dashboard:
1. Go to your project
2. Click on the deployment
3. View logs for any errors

## 🔄 Automatic Deployments

Railway automatically deploys when you:
1. Push to the main branch
2. Create a pull request (optional)

## 📊 Monitoring

Railway provides:
- **Uptime monitoring**
- **Resource usage** (CPU, memory)
- **Deployment logs**
- **Environment variable management**

## 🚀 Production Tips

1. **Use Railway's PostgreSQL** for the database
2. **Set up custom domains** in Railway dashboard
3. **Monitor resource usage** to avoid hitting limits
4. **Use Railway's secrets** for sensitive environment variables

## 🔗 Useful Links

- [Railway Documentation](https://docs.railway.app/)
- [Python on Railway](https://docs.railway.app/deploy/deployments/languages/python)
- [Environment Variables](https://docs.railway.app/deploy/environment-variables)
