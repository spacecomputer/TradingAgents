# TradingAgents SaaS - Multi-Agent Financial Trading Platform

## Project Overview
A comprehensive SaaS transformation of the TradingAgents CLI framework, featuring:
- **Web-based Interface**: Modern React/TypeScript frontend with responsive design
- **RESTful API**: Flask backend with SQLite database and WebSocket support
- **Real-time Analysis**: Live progress monitoring and result streaming
- **User Management**: Authentication, subscription tiers, and credit system
- **Multi-Agent AI**: Integration with existing TradingAgents framework

## Architecture

### Backend (Flask + SQLAlchemy + SocketIO)
- **Port**: 8000
- **Database**: SQLite (development), PostgreSQL (production)
- **Authentication**: Session-based with Google OAuth integration
- **Real-time**: WebSocket support for live analysis updates
- **API Endpoints**: Comprehensive REST API for all operations

### Frontend (React + TypeScript + Vite)
- **Port**: 5000
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS with custom components
- **State Management**: React Context for authentication
- **Real-time**: Socket.IO client for live updates

## Key Features

### User Management
- Email-based authentication with Google OAuth support
- Subscription tiers: Free, Pro, Enterprise
- Credit-based usage system
- User settings and preferences

### Analysis Management
- Create new analyses with configuration wizard
- Real-time progress monitoring with stage tracking
- Comprehensive report generation and viewing
- Analysis history and management

### Dashboard & Interface
- Modern, responsive web interface
- Real-time status updates and notifications
- Interactive charts and progress indicators
- Mobile-friendly design

## Development Status

### Phase 1: Core Infrastructure ✅
- [x] Project structure setup
- [x] Flask backend with models and routes
- [x] React frontend with authentication
- [x] Database integration
- [x] WebSocket support

### Phase 2: User Interface ✅
- [x] Login/authentication pages
- [x] Dashboard with statistics
- [x] Analysis wizard and management
- [x] Settings and subscription management
- [x] Real-time progress monitoring

### Phase 3: Integration & Testing 🔄
- [x] Backend API complete
- [x] Frontend components complete
- [ ] TradingAgents framework integration
- [ ] End-to-end testing
- [ ] Production deployment configuration

## Current Configuration

### Workflows
1. **TradingAgents SaaS Backend** (Port 8000) - ✅ Running
   - Flask API server with WebSocket support
   - SQLite database with user and analysis models
   - Authentication and analysis endpoints

2. **TradingAgents SaaS Frontend** (Port 5000) - 🔄 Setting up
   - React development server with Vite
   - Proxy configuration for API calls
   - Real-time WebSocket integration

### Environment Variables
- `FINNHUB_API_KEY`: Financial data API access
- `OPENAI_API_KEY`: LLM model access
- `DATABASE_URL`: Database connection (optional, defaults to SQLite)
- `SECRET_KEY`: Flask session security

## Development Setup

### Quick Start
```bash
# Backend
cd webapp/backend
python app.py

# Frontend (in new terminal)
cd webapp/frontend
npm install
npm run dev
```

### Full Development Environment
```bash
# Use the startup script
chmod +x webapp/start.sh
./webapp/start.sh
```

## User Preferences
- **Development Approach**: Modern web technologies with emphasis on user experience
- **Code Quality**: TypeScript for frontend, Python with proper error handling
- **Real-time Features**: WebSocket integration for live updates
- **Responsive Design**: Mobile-first approach with Tailwind CSS

## Technical Decisions

### Database Design
- **Users Table**: Authentication, subscription, and credit management
- **Analyses Table**: Analysis metadata, status, and results
- **JSON Fields**: Flexible configuration and report data storage

### API Design
- **RESTful Endpoints**: Standard HTTP methods for CRUD operations
- **WebSocket Events**: Real-time updates for analysis progress
- **Error Handling**: Comprehensive error responses with user-friendly messages

### Security
- **Session Management**: Flask-based sessions with secure configuration
- **CORS**: Configured for development and production environments
- **Input Validation**: Server-side validation for all user inputs

## Next Steps
1. Complete frontend workflow setup
2. Integrate TradingAgents CLI functionality
3. Implement background job processing
4. Add comprehensive error handling
5. Prepare production deployment configuration

## Notes
- Original CLI application remains functional
- Web interface designed as a comprehensive replacement
- Maintains all multi-agent functionality from original framework
- Scalable architecture for future enhancements