# Python Debug Tool - Frontend

A modern React frontend for the Python Debug Tool built with Vite, following the React development guide best practices.

## Features

- **Project Selection**: Select local directories or Git repositories for analysis
- **File Confirmation**: Interactive file tree with selection controls and analysis settings
- **Real-time Processing**: Live progress tracking with phase indicators and statistics
- **Dashboard**: Comprehensive analysis results with risk distribution and recommendations
- **History Management**: View and manage previous analysis runs
- **Neo4j Integration**: Query and visualize knowledge graph data (coming soon)
- **Export Capabilities**: Export results in various formats (coming soon)

## Tech Stack

- **React 19** - UI framework
- **Vite** - Build tool and development server
- **Ant Design 5** - UI component library
- **React Router 6** - Client-side routing
- **Axios** - HTTP client for API communication

## Project Structure

```
src/
├── components/           # Reusable UI components
│   ├── Header.jsx       # Application header
│   └── Sidebar.jsx      # Navigation sidebar
├── pages/               # Route-level components
│   ├── ProjectSelector.jsx    # Project/repo selection
│   ├── FileConfirmation.jsx   # File selection interface
│   ├── Processing.jsx         # Real-time processing view
│   ├── Dashboard.jsx          # Analysis results dashboard
│   ├── History.jsx            # Analysis history management
│   ├── Neo4jGraph.jsx         # Knowledge graph interface
│   ├── FileExplorer.jsx       # File exploration
│   └── ErrorDashboard.jsx     # Error monitoring
├── hooks/               # Custom React hooks
│   └── useApi.js       # API communication hooks
├── utils/              # Utility functions
│   └── helpers.js      # Helper functions
├── services/           # API service layer
│   └── api.js         # Backend API communication
├── context/            # React context providers
│   └── AppContext.jsx # Global application state
├── assets/             # Static assets
└── styles/             # CSS files
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python Debug Tool backend running on port 8080

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

The application will open at `http://localhost:3015`.

### Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8080

# Development Settings
VITE_DEBUG_MODE=true
VITE_ENABLE_ERROR_REPORTING=true

# Feature Flags
VITE_ENABLE_NEO4J=true
VITE_ENABLE_IDE_INTEGRATION=true
VITE_ENABLE_EXPORT=true
```

## Backend Integration

The frontend communicates with the FastAPI backend for:

- Project analysis and file discovery
- Processing management and status updates
- Results storage and retrieval
- Neo4j graph data access (when available)
- Export functionality

### API Endpoints (Pseudocode)

```javascript
// Project analysis
POST /api/projects/analyze
GET  /api/processing/status/{runId}

// File operations
GET  /api/files?path={path}&python_only={boolean}
GET  /api/filesystem/browse?path={path}

// Results management
GET  /api/runs
GET  /api/runs/{runId}
GET  /api/runs/{runId}/dashboard
DELETE /api/runs/{runId}

// Export and IDE integration
GET  /api/export/{runId}?format={format}
POST /api/ide/open
```

## Development Workflow

1. **Component Development**: Create components in `src/components/` using `.jsx` extension
2. **Page Development**: Create route-level components in `src/pages/`
3. **API Integration**: Add API calls to `src/services/api.js` with pseudocode comments
4. **State Management**: Use React Context for global state, custom hooks for complex logic
5. **Styling**: Use Ant Design components with custom CSS in `src/App.css`

## Component Guidelines

- Use `.jsx` extension for React components
- Use `.js` extension for utility functions and services
- Follow functional component patterns with hooks
- Implement proper error handling with loading states
- Use Ant Design components for consistent UI
- Include proper TypeScript-like prop validation where needed

## Building for Production

```bash
npm run build
```

Build artifacts will be in the `dist/` directory.

## Available Scripts

- `npm run dev` - Start development server on port 3015
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Architecture Notes

- **State Management**: React Context API with useReducer for complex state
- **API Layer**: Centralized API service with error handling and retry logic
- **Routing**: React Router with lazy loading for optimal performance
- **Error Handling**: Global error boundaries with user-friendly error messages
- **Performance**: Optimized bundle splitting and lazy loading

## Future Enhancements

- Complete Dashboard implementation with detailed analysis results
- Neo4j graph visualization with interactive network diagrams
- File Explorer with syntax highlighting and IDE integration
- Error Dashboard with real-time monitoring
- Export functionality for multiple formats
- WebSocket integration for real-time updates

## Contributing

1. Follow the React development guide best practices
2. Use Ant Design components consistently
3. Maintain proper component structure and naming
4. Add proper error handling and loading states
5. Update documentation for new features

## License

This project is part of the Python Debug Tool suite.
