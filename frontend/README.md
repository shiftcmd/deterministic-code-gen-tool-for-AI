# Deterministic AI Framework - Frontend

A React-based web interface for the Deterministic AI Framework that provides code analysis, validation, and knowledge graph visualization.

## Features

- **Project Selection**: Select local directories or clone Git repositories for analysis
- **File Confirmation**: Interactive file tree with selection controls and analysis settings
- **Real-time Processing**: Live progress tracking with phase indicators and statistics  
- **Dashboard**: Comprehensive analysis results with risk distribution, file analysis, and recommendations
- **History Management**: View and manage previous analysis runs
- **Neo4j Integration**: Query and visualize knowledge graph data
- **Export Capabilities**: Export results in JSON and PDF formats

## Prerequisites

- Node.js 16+ and npm
- Python 3.8+ (for backend)
- Backend API server running on port 8000

## Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

The application will open at `http://localhost:3000`.

## Backend Requirements

The frontend requires the backend API server to be running. Start it with:

```bash
cd ..
python backend_api.py
```

The backend will start on `http://localhost:8000`.

## Project Structure

```
src/
├── components/           # React components
│   ├── Dashboard/       # Analysis results dashboard
│   ├── FileConfirmation/ # File selection interface
│   ├── History/         # Analysis history management
│   ├── Layout/          # Header and sidebar components
│   ├── Neo4j/           # Knowledge graph interface
│   ├── Processing/      # Real-time processing view
│   └── ProjectSelector/ # Project/repo selection
├── context/             # React context providers
│   └── FrameworkContext.js
├── services/            # API service layer
│   └── api.js
├── App.js              # Main application component
├── App.css             # Global styles
└── index.js            # Application entry point
```

## API Integration

The frontend communicates with the backend API for:

- Project analysis and file discovery
- Processing management and status updates
- Results storage and retrieval
- Neo4j graph data access
- Export functionality

## Usage

1. **Start New Analysis**:
   - Select project source (local folder or Git repo)
   - Browse and select project directory
   - Review project statistics

2. **Confirm Files**:
   - View interactive file tree
   - Select Python files for analysis
   - Configure analysis settings
   - Start framework processing

3. **Monitor Processing**:
   - Real-time progress tracking
   - Phase-by-phase status updates
   - Live processing logs
   - Analysis statistics

4. **View Results**:
   - Risk distribution overview
   - Detailed file analysis
   - Actionable recommendations
   - Neo4j knowledge graph

5. **Manage History**:
   - View previous analysis runs
   - Access saved dashboards
   - Delete old analyses
   - Export results

## Configuration

The frontend can be configured through:

- Environment variables in `.env`
- API base URL in `src/services/api.js`
- Theme settings in `src/App.js`

## Development

### Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run test suite
- `npm eject` - Eject from Create React App

### Component Development

Each component follows Ant Design patterns and includes:

- TypeScript-like prop validation
- Responsive design
- Loading states
- Error handling
- Accessibility features

## Production Build

To build for production:

```bash
npm run build
```

The build artifacts will be in the `build/` directory.

## Technologies

- **React 18** - UI framework
- **Ant Design 5** - Component library
- **React Router 6** - Navigation
- **Axios** - HTTP client
- **WebSocket** - Real-time updates

## Architecture

The frontend follows a component-based architecture with:

- **Context API** for state management
- **Service layer** for API abstraction  
- **Responsive design** for mobile support
- **Real-time updates** via WebSocket
- **Modular components** for maintainability

## Contributing

1. Follow React best practices
2. Use Ant Design components
3. Maintain responsive design
4. Add proper error handling
5. Update documentation

## Troubleshooting

### Backend Connection Issues
- Ensure backend is running on port 8000
- Check CORS configuration
- Verify API endpoints in browser network tab

### Build Issues
- Clear npm cache: `npm cache clean --force`
- Delete node_modules and reinstall
- Check Node.js version compatibility

### Performance Issues
- Use React DevTools Profiler
- Check for unnecessary re-renders
- Optimize large file tree rendering

## License

This project is part of the Deterministic AI Framework.