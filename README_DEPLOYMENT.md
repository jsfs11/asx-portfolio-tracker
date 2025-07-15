# 🚀 Deployment Guide

## 🔐 API Key Security

### **IMPORTANT: Never commit your API key to GitHub!**

### Step 1: Set up Environment Variables
```bash
# Copy the example file
cp .env.example .env

# Edit .env with your actual API key
echo "EODHD_API_KEY=your_actual_key_here" > .env
```

### Step 2: Install Dependencies
```bash
pip install python-dotenv
pip install -r requirements_streamlit.txt
```

## 📁 Repository Setup

### **What Gets Committed:**
✅ All Python files  
✅ requirements_streamlit.txt  
✅ .env.example (template)  
✅ .gitignore  
✅ README files  

### **What Stays Private:**
🔒 .env (your actual API key)  
🔒 config.py (if contains sensitive data)  
🔒 portfolio.db (your personal data)  
🔒 Generated charts/exports  

## 🌐 Deployment Options

### **Option 1: GitHub Repository**
```bash
# Initialize git
git init
git add .
git commit -m "Initial commit - ASX Portfolio Tracker"

# Create GitHub repo, then:
git remote add origin https://github.com/yourusername/asx-portfolio-tracker.git
git push -u origin main
```

**User setup:**
```bash
git clone https://github.com/yourusername/asx-portfolio-tracker.git
cd asx-portfolio-tracker
cp .env.example .env
# Edit .env with your API key (or use 'demo')
pip install -r requirements_streamlit.txt
streamlit run streamlit_app.py
```

### **Option 2: Streamlit Cloud (Public)**
1. Push to GitHub (without API key)
2. Connect to Streamlit Cloud
3. Add API key in Streamlit Cloud secrets
4. Share URL: `https://your-app.streamlit.app`

**Streamlit Cloud Secrets:**
```toml
# In Streamlit Cloud dashboard
[secrets]
EODHD_API_KEY = "your_actual_key_here"
```

### **Option 3: Private Docker Container**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements_streamlit.txt
EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py"]
```

**Build and share:**
```bash
# Build container
docker build -t asx-portfolio .

# Save to file
docker save asx-portfolio:latest | gzip > asx-portfolio.tar.gz

# User loads and runs:
docker load < asx-portfolio.tar.gz
docker run -e EODHD_API_KEY=your_key_here -p 8501:8501 asx-portfolio
```

## 💻 Cross-Platform Setup

### **macOS/Linux Instructions:**
1. **Install Python 3.9+** (if not already installed)
2. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/asx-portfolio-tracker.git
   cd asx-portfolio-tracker
   ```
3. **Set up API key:**
   ```bash
   cp .env.example .env
   # Edit .env file and add: EODHD_API_KEY=your_key_here
   ```
4. **Install and run:**
   ```bash
   pip install -r requirements_streamlit.txt
   streamlit run streamlit_app.py
   ```

### **Create run script:**
```bash
#!/bin/bash
# save as run_app.sh
cd "$(dirname "$0")"
echo "Starting ASX Portfolio Tracker..."
streamlit run streamlit_app.py
```

Make executable: `chmod +x run_app.sh`

## 🔧 Configuration Options

### **API Key Sources (in order of priority):**
1. `.env` file: `EODHD_API_KEY=your_key`
2. Environment variable: `export EODHD_API_KEY=your_key`
3. Streamlit secrets (if deployed)
4. Fallback: `"demo"` (limited functionality)

### **Demo Mode:**
- Works without API key
- Uses sample prices
- Limited to cached data
- Perfect for testing

## 🎯 Recommended Approach

**For Maximum Security & Ease:**

1. **GitHub Repository** (public code, private keys)
2. **Environment variables** for API keys
3. **Clear documentation** for users
4. **Demo mode** as fallback

Users get:
- ✅ Easy setup process
- ✅ Secure API key management
- ✅ All latest features
- ✅ No security concerns

## 🚨 Security Checklist

Before sharing:
- [ ] .env file NOT in git
- [ ] .gitignore includes .env
- [ ] API key moved to environment variables
- [ ] No sensitive data in code
- [ ] Demo mode works without API key
- [ ] Clear setup instructions provided

**Ready to create the GitHub repository with these security measures?**