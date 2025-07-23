# Complete Debugging Workflow Setup

## 🚀 **Current Tech Stack**

### Backend (Python/FastAPI)
- **Framework**: FastAPI with Uvicorn ASGI server
- **Port**: 8080 (configured to match frontend expectations)
- **Features**: CORS enabled, hot reload, debug logging
- **Dependencies**: All installed in `venv/` virtual environment

### Frontend (React)
- **Framework**: React 18.2.0 with Create React App
- **UI Library**: Ant Design
- **HTTP Client**: Axios
- **Port**: 3000 (default CRA port)
- **Proxy**: Configured to proxy API calls to `http://localhost:8080`

## 🔧 **VS Code Debug Configuration**

### Debug Launch Options (.vscode/launch.json):
1. **"FastAPI Backend"** - Runs Python backend with debugging
2. **"React Frontend"** - Launches Chrome with React app
3. **"🚀 Full Stack Debug"** - Compound configuration running both simultaneously

### Tasks (.vscode/tasks.json):
1. **"🚀 Start Full Stack (Concurrently)"** - Starts both servers with colored output
2. **"Start Backend (Python/FastAPI)"** - Backend only
3. **"npm: start - frontend"** - Frontend only
4. **"Install Frontend Dependencies"** / **"Install Backend Dependencies"**

## 🎯 **Quick Start Options**

### Option 1: VS Code Debug (Recommended)
1. Open VS Code Debug panel (Ctrl+Shift+D)
2. Select "🚀 Full Stack Debug" from dropdown
3. Press F5 or click the green play button
4. Both backend and frontend will start with full debugging support

### Option 2: VS Code Tasks
1. Open Command Palette (Ctrl+Shift+P)
2. Type "Tasks: Run Task"
3. Select "🚀 Start Full Stack (Concurrently)"
4. Both servers start in integrated terminal with colored output

### Option 3: NPM Scripts
```bash
# Start both frontend and backend together
npm run dev

# Or start them separately:
npm run start:backend
npm run start:frontend
```

### Option 4: Manual Terminal
```bash
# Terminal 1 - Backend
source venv/bin/activate
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload

# Terminal 2 - Frontend  
cd frontend
npm start
```

## 🔍 **Environment Variables**

### Backend (.env in root):
- All API keys configured (OpenAI, Anthropic, Perplexity, etc.)
- Neo4j, Supabase, and other service credentials

### Frontend (frontend/.env):
- `REACT_APP_API_BASE_URL=http://localhost:8080/api`
- Debug and error reporting settings

## 🧪 **Testing Access**

### Backend Health Checks:
- Root: http://localhost:8080/
- Health: http://localhost:8080/health
- API Health: http://localhost:8080/api/health

### Frontend:
- Main App: http://localhost:3000/
- Automatically proxies API calls to backend

## 🛠 **Debugging Features**

### Backend Debugging:
- **Breakpoints**: Set in Python files, they'll be hit during API calls
- **Hot Reload**: Code changes automatically restart the server
- **Debug Logging**: Detailed uvicorn logs with `--log-level debug`
- **Environment**: Virtual environment automatically activated

### Frontend Debugging:
- **Chrome DevTools**: Full React DevTools support
- **Breakpoints**: Set in JavaScript/React files
- **Hot Reload**: Changes immediately reflected in browser
- **Network Tab**: Monitor API calls to backend

### Full Stack Debugging:
- **Simultaneous**: Debug both frontend and backend at the same time
- **Breakpoint Flow**: Hit frontend breakpoint → trigger API call → hit backend breakpoint
- **Live Data Flow**: Watch data flow from React → FastAPI → Database

## 📁 **Port Configuration**

| Service | Port | URL |
|---------|------|-----|
| FastAPI Backend | 8080 | http://localhost:8080 |
| React Frontend | 3000 | http://localhost:3000 |
| Neo4j (if running) | 7687 | bolt://localhost:7687 |
| PostgreSQL (if running) | 5432 | localhost:5432 |

## 🚨 **Troubleshooting**

### Backend Won't Start:
1. Ensure virtual environment is activated: `source venv/bin/activate`
2. Check Python dependencies: `pip install -r requirements.txt`
3. Verify Python path: `which python` should show venv path
4. Check for port conflicts: `lsof -i :8080`

### Frontend Won't Start:
1. Install dependencies: `cd frontend && npm install`
2. Check Node version: `node --version` (should be 14+)
3. Clear cache: `npm start -- --reset-cache`

### API Connection Issues:
1. Verify backend is running on port 8080
2. Check CORS settings in `backend/main.py`
3. Verify proxy setting in `frontend/package.json`
4. Test direct API calls: `curl http://localhost:8080/health`

## 🎉 **Success Indicators**

✅ Backend running: `{"message": "Python Debug Tool API is running", "version": "0.1.0"}`
✅ Frontend running: React app loads at http://localhost:3000
✅ API connectivity: Frontend can call backend endpoints
✅ Debugging active: Breakpoints work in both frontend and backend code

This setup provides a complete, professional debugging environment for full-stack development! 