# 🚀 Python Debug Tool - Current Start Guide

## ✅ **Quick Start (Recommended)**

```bash
# Kill any existing processes and start all 3 services
npm run clean-start
```

This starts:
- **Backend API** (port 8080) - FastAPI server
- **Frontend** (port 3000+) - React development server  
- **Orchestrator Service** (port 8078) - Analysis pipeline manager

## 🎯 **Available Commands**

### Starting Services
```bash
npm run dev              # Start all 3 services with concurrently
npm run clean-start      # Kill conflicts then start fresh
npm run start:backend    # Backend API only
npm run start:frontend   # Frontend only
```

### Managing Services
```bash
npm run kill            # Stop all services
npm run status          # Check what's running
npm run health          # Test service health
npm run ports           # Check port usage
```

### Health Check URLs
- **Backend**: http://localhost:8080/health
- **Frontend**: http://localhost:3000/ (or next available port)
- **Orchestrator**: http://localhost:8078/health

## 🔧 **Port Configuration**

| Service | Port | Purpose |
|---------|------|---------|
| Backend API | 8080 | Main FastAPI application |
| Frontend | 3000+ | React development server |
| Orchestrator | 8078 | Analysis pipeline service |

## 🚨 **Troubleshooting**

### If analysis tool shows "Service Unavailable":
1. Check if orchestrator is running: `curl http://localhost:8078/health`
2. If not running, restart services: `npm run clean-start`

### If ports are in use:
```bash
npm run ports           # Check what's using ports
npm run kill           # Kill our services
npm run clean-start    # Start fresh
```

### Manual cleanup:
```bash
pkill -f 'uvicorn.*main:app'        # Kill backend
pkill -f 'vite'                     # Kill frontend  
pkill -f 'orchestrator.*main.py'    # Kill orchestrator
```

## ✅ **Success Indicators**

When everything is working:
- Backend: `{"status":"healthy","service":"python-debug-tool"}`
- Frontend: Shows React app in browser
- Orchestrator: `{"status":"healthy","timestamp":"..."}`
- Analysis tool works without "Service Unavailable" errors

## 🎉 **Updated Features**

✅ **Three-service startup** - All services start together  
✅ **Automatic orchestrator** - No manual orchestrator startup needed  
✅ **Improved kill script** - Stops all services cleanly  
✅ **Port conflict prevention** - Clean start kills conflicting processes  

---

**Date:** July 24, 2025  
**Status:** Current and tested ✅