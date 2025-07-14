# 🚀 Secure Deployment Guide

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

## 🍎 Mac Setup Instructions

### **Simple Instructions:**
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
