# 🚀 Streamlit Web Interface Setup

## Quick Start

### 1. Install Dependencies
```bash
# Install Streamlit requirements
pip install -r requirements_streamlit.txt

# Or install manually
pip install streamlit plotly yfinance pandas numpy requests
```

### 2. Run the Web App
```bash
# Navigate to the folder
cd asx-portfolio-tracker

# Start the web interface
streamlit run streamlit_app.py
```

### 3. Open in Browser
- The app will automatically open at `http://localhost:8501`
- If not, manually navigate to that URL

## 📱 Web Interface Features

### 🏠 **Dashboard**
- Portfolio overview with key metrics
- Interactive pie chart showing allocation
- Performance bar chart by stock
- Real-time positions table
- Database statistics

### 💰 **Add Transaction**
- User-friendly form for stock transactions
- Automatic brokerage fee calculation
- Transaction preview before submission
- Input validation and error handling

### 📈 **Update Prices**
- One-click price updates from EODHD API
- API usage tracking (20 calls/day limit)
- Force update option to bypass limits
- Clear status indicators

### 📊 **Performance Analysis**
- **ASX200 Comparison**: Interactive benchmark charts
- **Attribution Analysis**: Which stocks help/hurt performance
- **Rolling Performance**: 1D, 7D, 30D trend analysis
- **Export Functions**: CSV downloads for all data

### ⚙️ **Settings**
- API configuration overview
- Database management tools
- Data clearing functionality (with safety checks)
- App information and status

## 🔧 Technical Features

### **Non-Destructive Design**
- All original CLI tools remain fully functional
- Web interface imports existing modules
- Same database, same analysis - just better UI
- Zero disruption to current workflow

### **Modern UI Components**
- Responsive design that works on all devices
- Interactive Plotly charts with hover details
- Real-time data updates
- Clean, professional styling

### **Data Safety**
- Input validation on all forms
- Confirmation dialogs for destructive actions
- Automatic data backup recommendations
- Error handling with user-friendly messages

## 🍎 Sharing Instructions

### **Installation Package**
Create a simple setup package:

1. **Create setup folder:**
```
ASX_Portfolio_Tracker/
├── All your .py files
├── requirements_streamlit.txt
├── README_STREAMLIT.md
├── run_app.command (Mac script)
└── portfolio.db (optional sample data)
```

2. **Create `run_app.command`:**
```bash
#!/bin/bash
cd "$(dirname "$0")"
streamlit run streamlit_app.py
```

3. **Make it executable:**
```bash
chmod +x run_app.command
```

### **For Mac Users**
1. Install Python 3.9+ (if not already installed)
2. Open Terminal and run: `pip install streamlit plotly yfinance pandas numpy requests`
3. Double-click `run_app.command` to start the app
4. Browser will open automatically to the dashboard

### **Even Simpler: Docker Option**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements_streamlit.txt
EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py"]
```

Users just need to:
1. Install Docker Desktop
2. Run: `docker run -p 8501:8501 your-portfolio-app`
3. Open browser to `localhost:8501`

## 🎯 Benefits Over CLI

### **User Experience**
- No command line knowledge required
- Visual feedback for all actions
- Point-and-click interface
- Real-time data visualization

### **Accessibility**
- Works on any device with a browser
- Responsive design for mobile/tablet
- Intuitive navigation
- Built-in help text and tooltips

### **Sharing & Collaboration**
- Easy to demonstrate to others
- Screenshots are meaningful
- Can be hosted online for remote access
- Professional presentation quality

## 🔍 Troubleshooting

### **Common Issues**
- **Port already in use**: Change port with `streamlit run streamlit_app.py --server.port 8502`
- **Import errors**: Ensure all original .py files are in the same directory
- **Database not found**: Make sure portfolio.db exists (run CLI tool first)

### **Performance**
- Large datasets may take a moment to load
- Charts are generated on-demand for better performance
- API calls are the same as CLI - no additional limitations

## 📊 Feature Comparison

| Feature | CLI Tools | Streamlit Web |
|---------|-----------|---------------|
| Portfolio tracking | ✅ | ✅ |
| Price updates | ✅ | ✅ |
| Performance analysis | ✅ | ✅ |
| Data export | ✅ | ✅ |
| User interface | Terminal | Modern Web |
| Ease of use | Technical | User-friendly |
| Sharing | Screenshots | Live demo |
| Charts | Static files | Interactive |

## 🚀 Next Steps

1. **Test the interface** with your existing data
2. **Share with others** using the setup instructions
3. **Customize styling** by editing the CSS in streamlit_app.py
4. **Add features** by extending the existing pages
5. **Host online** using Streamlit Cloud for remote access

The web interface provides all the power of CLI tools with a modern, user-friendly experience that's perfect for sharing with users who prefer point-and-click interfaces!