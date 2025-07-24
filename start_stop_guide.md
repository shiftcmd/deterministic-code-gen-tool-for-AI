# 🚀 Complete Start/Stop Task Guide - **DEPRECATED**

⚠️ **This guide is outdated. The current npm scripts have been updated to include orchestrator service.**

**Current working command:** `npm run dev` now starts all 3 services (backend, frontend, orchestrator)

---

## 🎯 **New VS Code Tasks Available**

### 🚀 **Starting Services**

1. **"🚀 Start Full Stack (Concurrently)"** - Start both with colored output
2. **"🧹 Clean Start (Kill Conflicts & Start Fresh)"** - Force kill any conflicts and start clean
3. **"🔄 Restart Full Stack"** - Stop everything then start fresh
4. **"⚡ Quick Backend Only"** - Backend only (FastAPI)
5. **"⚡ Quick Frontend Only"** - Frontend only (React)

### 🛑 **Stopping Services**

1. **"🛑 Kill All Development Servers"** - Stop all uvicorn, react-scripts, and node processes

### 🔍 **Diagnostics**

1. **"🔍 Check Port Usage"** - See what's using ports 3000, 8080, etc.
2. **"🩺 Health Check All Services"** - Test if services are responding

## 💻 **NPM Scripts (Command Line)**

```bash
# Start both services together
npm run dev

# Start individual services
npm run start:backend    # FastAPI backend only
npm run start:frontend   # React frontend only

# Management commands
npm run kill            # Stop all development servers
npm run clean-start     # Kill then start fresh
npm run ports          # Check port usage
npm run health         # Test service health

# Setup
npm run install:all    # Install all dependencies
```

## 🎮 **How to Use in VS Code**

### Method 1: Command Palette
1. Press `Ctrl+Shift+P`
2. Type "Tasks: Run Task"
3. Choose from the task list:
   - 🧹 Clean Start (Kill Conflicts & Start Fresh)
   - 🚀 Start Full Stack (Concurrently)
   - 🛑 Kill All Development Servers
   - 🔍 Check Port Usage
   - 🩺 Health Check All Services

### Method 2: Debug Panel
1. Press `Ctrl+Shift+D` (Debug view)
2. Select "🚀 Full Stack Debug"
3. Press `F5` - automatically kills conflicts and starts fresh

## 🔧 **Port Management**

### Our Application Ports:
- **Backend (FastAPI)**: 8080
- **Frontend (React)**: 3000

### Automatic Conflict Resolution:
- **Clean Start** task automatically kills processes on ports 8080 and 3000
- **Launch configurations** include pre-launch tasks to clear conflicts
- All scripts check for virtual environment activation

## 🛠 **Features Added**

### ✅ **Port Conflict Prevention**
- Automatically kills processes on target ports before starting
- Uses `lsof` to identify and terminate port conflicts
- Graceful fallback if processes don't exist

### ✅ **Environment Management**
- Automatically activates Python virtual environment
- Sets `BROWSER=none` to prevent auto-opening browsers
- Proper working directory handling

### ✅ **Process Management**
- Uses `pkill` with specific patterns to target only our processes
- Avoids killing system processes or other projects
- Includes safety fallbacks (`|| true`)

### ✅ **Visual Feedback**
- Colored output for backend (blue) and frontend (green)
- Clear task names with emojis for easy identification
- Detailed status messages and error handling

## 🚨 **Troubleshooting Commands**

### If something goes wrong:
```bash
# Check what's using your ports
npm run ports

# Check service health
npm run health

# Force kill everything and start clean
npm run clean-start

# Manual process cleanup
pkill -f "uvicorn.*main:app"
pkill -f "react-scripts start"
```

### VS Code Task Issues:
1. Open Command Palette → "Tasks: Run Task"
2. Select "🔍 Check Port Usage" to diagnose
3. Select "🛑 Kill All Development Servers" to clean up
4. Select "🧹 Clean Start" to restart everything

## 🎉 **Success Indicators**

✅ **Backend**: `curl http://localhost:8080/health` returns `{"status":"healthy","service":"python-debug-tool"}`
✅ **Frontend**: `curl -I http://localhost:3000/` returns HTTP 200 or 302
✅ **Both**: `npm run health` shows both services responding
✅ **Processes**: `ps aux | grep -E "(uvicorn|react-scripts)"` shows both processes

## 🔄 **Recommended Workflow**

1. **Start of Day**: `Ctrl+Shift+P` → "Tasks: Run Task" → "🧹 Clean Start"
2. **During Development**: Use VS Code Debug Panel (`Ctrl+Shift+D` → "🚀 Full Stack Debug")
3. **End of Day**: `Ctrl+Shift+P` → "Tasks: Run Task" → "🛑 Kill All Development Servers"
4. **If Issues**: `npm run ports` then `npm run clean-start`

This setup ensures you never have port conflicts and can quickly start/stop your development environment! 