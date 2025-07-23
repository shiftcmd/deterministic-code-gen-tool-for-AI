# 🔛 Simple ON/OFF Guide for Your Development Environment

## 🚀 **Turn Everything ON**

### **Method 1: VS Code (Easiest)**
1. Press `Ctrl+Shift+P`
2. Type "Tasks: Run Task" 
3. Select **"🧹 Clean Start (Kill Conflicts & Start Fresh)"**
4. Watch the terminal for colored output (blue=backend, green=frontend)

### **Method 2: Command Line**
```bash
npm run clean-start
```

### **Method 3: VS Code Debug Panel**
1. Press `Ctrl+Shift+D` (Debug view)
2. Select "🚀 Full Stack Debug"
3. Press `F5`

---

## 🛑 **Turn Everything OFF**

### **Method 1: VS Code**
1. Press `Ctrl+Shift+P`
2. Type "Tasks: Run Task"
3. Select **"🛑 Kill All Development Servers"**

### **Method 2: Command Line**
```bash
npm run kill
```

### **Method 3: Manual Kill**
```bash
pkill -f 'uvicorn.*main:app'     # Kill backend
pkill -f 'react-scripts start'  # Kill frontend
```

---

## 🔄 **Restart Everything**

### **Method 1: VS Code**
1. Press `Ctrl+Shift+P`
2. Type "Tasks: Run Task"
3. Select **"🔄 Restart Full Stack"**

### **Method 2: Command Line**
```bash
npm run kill && sleep 2 && npm run clean-start
```

---

## 🧪 **Check Status**

### **Health Check**
```bash
npm run health
```
**Expected Output:**
```
{"status":"healthy","service":"python-debug-tool"} Frontend: HTTP 200
```

### **Port Check**
```bash
npm run ports
```
**Expected Output:**
```
tcp    0.0.0.0:8080    LISTEN    # Backend
tcp6   :::3000         LISTEN    # Frontend
```

### **Process Check**
```bash
ps aux | grep -E "(uvicorn|react-scripts)" | grep -v grep
```

---

## 🎯 **URLs to Access**

- **Frontend**: http://localhost:3000/
- **Backend API**: http://localhost:8080/
- **Backend Health**: http://localhost:8080/health
- **API Endpoints**: http://localhost:8080/api/

---

## 🚨 **If Something Goes Wrong**

### **Common Issues & Fixes:**

#### ❌ **Port Already in Use**
```bash
npm run clean-start    # Force kills conflicts and starts fresh
```

#### ❌ **Backend Won't Start**
```bash
# Check virtual environment
source venv/bin/activate
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

#### ❌ **Frontend Won't Start** 
```bash
cd frontend
npm install    # Install dependencies
npm start      # Start manually
```

#### ❌ **Both Services Stuck**
```bash
npm run kill          # Kill everything
sleep 2               # Wait 
npm run clean-start   # Start fresh
```

---

## 🏆 **Daily Workflow**

### **Start of Day:**
```bash
npm run clean-start    # Turn ON everything (cleans up any conflicts)
```

### **During Development:**
- Use VS Code Debug Panel (`Ctrl+Shift+D` → "🚀 Full Stack Debug")
- Set breakpoints in both Python and React code
- Both will hot-reload when you make changes

### **End of Day:**
```bash
npm run kill           # Turn OFF everything
```

### **If Issues:**
```bash
npm run ports          # Check what's using your ports
npm run health         # Check if services are responding  
npm run clean-start    # Nuclear option - kill and restart
```

---

## ⚡ **Quick Reference**

| Task | Command | VS Code Task |
|------|---------|--------------|
| Turn ON | `npm run clean-start` | "🧹 Clean Start" |
| Turn OFF | `npm run kill` | "🛑 Kill All Development Servers" |
| Restart | `npm run kill && npm run clean-start` | "🔄 Restart Full Stack" |
| Check Health | `npm run health` | "🩺 Health Check All Services" |
| Check Ports | `npm run ports` | "🔍 Check Port Usage" |

**The "Clean Start" option is your best friend - it handles all conflicts automatically!** 🚀 