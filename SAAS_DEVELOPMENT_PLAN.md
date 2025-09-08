# TradingAgents SaaS Platform - Development Plan

## 🎯 **Project Overview**

Transform the TradingAgents CLI into a modern, scalable SaaS web application with Google OAuth authentication, real-time analysis monitoring, and subscription-based access to multi-agent financial trading insights.

## 📋 **Development Phases**

### **Phase 1: Foundation & Architecture**

#### 1.1 Authentication System
- **Replit Auth Integration**: Primary authentication provider
- **Google OAuth Setup**: 
  - Configure Google Cloud Console OAuth client
  - Store OAuth secrets in Replit environment
  - Set up redirect URIs: `https://$REPLIT_DEV_DOMAIN/oauth2callback`
- **User Management**:
  - User profiles with trading preferences
  - API key management for users' own LLM providers
  - Subscription tiers (Free, Pro, Enterprise)

#### 1.2 Technology Stack
- **Frontend**: React with TypeScript
  - Tailwind CSS for responsive design
  - Socket.IO for real-time updates
  - Chart.js for data visualization
  - Framer Motion for animations
- **Backend**: Flask with SQLAlchemy
  - RESTful API + WebSockets for real-time communication
  - Background job processing with Celery/Redis
  - PostgreSQL for user data and analysis history
- **Infrastructure**:
  - Replit deployments for hosting
  - Redis for caching and session management
  - Built-in PostgreSQL for data persistence

### **Phase 2: Core Features Implementation**

#### 2.1 Application Structure
```
webapp/
├── backend/
│   ├── app.py                 # Flask application entry point
│   ├── models/
│   │   ├── user.py           # User model and authentication
│   │   ├── analysis.py       # Analysis records and status
│   │   └── subscription.py   # Subscription management
│   ├── routes/
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── api.py            # Analysis API endpoints
│   │   └── webhooks.py       # Payment and notification webhooks
│   ├── services/
│   │   ├── analysis_service.py # TradingAgents integration
│   │   └── notification_service.py # Email/alert service
│   └── utils/
│       ├── auth_utils.py     # Authentication helpers
│       └── validation.py     # Input validation
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.tsx     # Main dashboard
│   │   │   ├── AnalysisWizard.tsx # Analysis configuration
│   │   │   ├── ProgressMonitor.tsx # Real-time analysis tracking
│   │   │   └── ReportViewer.tsx   # Analysis results display
│   │   ├── pages/
│   │   │   ├── Login.tsx         # Authentication page
│   │   │   ├── Dashboard.tsx     # User dashboard
│   │   │   ├── Analysis.tsx      # Analysis management
│   │   │   └── Settings.tsx      # Account settings
│   │   ├── services/
│   │   │   ├── api.ts           # API client
│   │   │   └── websocket.ts     # Real-time communication
│   │   └── utils/
│   │       ├── auth.ts          # Authentication utilities
│   │       └── formatting.ts    # Data formatting helpers
│   ├── package.json
│   └── vite.config.ts
└── shared/
    ├── types.ts              # Shared TypeScript types
    └── constants.ts          # Application constants
```

#### 2.2 User Experience Flow

**CLI → Web UI Transformation:**

1. **Ticker Selection** → **Enhanced Stock Picker**
   - Searchable dropdown with autocomplete
   - Recent/favorite tickers saved per user
   - Multi-ticker batch analysis (Pro feature)
   - Market sector filters and trending stocks

2. **Date Selection** → **Interactive Date Range Picker**
   - Calendar widget with market hours awareness
   - Preset ranges (Today, Last Week, Last Month)
   - Historical backtesting periods
   - Market closure notifications

3. **Analyst Selection** → **Agent Configuration Panel**
   - Visual agent selector with descriptions and capabilities
   - Preset configurations (Conservative, Balanced, Aggressive)
   - Custom agent combinations (Pro feature)
   - Agent performance history

4. **Research Depth** → **Analysis Intensity Slider**
   - Visual representation of depth levels
   - Time/cost estimates with credit consumption
   - Quality vs speed trade-offs
   - Historical analysis time tracking

5. **LLM Provider** → **Model Configuration Dashboard**
   - Provider selection with API key validation
   - Model comparison table with costs
   - Performance benchmarks
   - Default configurations per subscription tier

#### 2.3 Real-Time Analysis Experience

**Live Analysis Dashboard Components:**
```typescript
interface AnalysisState {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: {
    currentStage: string;
    completedStages: string[];
    totalStages: number;
    estimatedTimeRemaining: number;
  };
  agents: {
    name: string;
    status: 'pending' | 'active' | 'completed';
    currentTask: string;
    insights: string[];
  }[];
  report: {
    sections: ReportSection[];
    keyFindings: string[];
    recommendation: 'BUY' | 'SELL' | 'HOLD';
    confidence: number;
  };
}
```

### **Phase 3: Advanced Features**

#### 3.1 Subscription Tiers & Features

**Free Tier:**
- 5 analyses per month
- Basic agents only (Market, News)
- 24-hour report retention
- Community LLM models only
- Email support

**Pro Tier ($29/month):**
- 100 analyses per month
- All agents available
- Unlimited report storage
- Priority processing queue
- API access (100 calls/day)
- Custom LLM providers
- Batch analysis capabilities
- Priority support

**Enterprise Tier (Custom Pricing):**
- Unlimited analyses
- Custom agent configurations
- White-label options
- Dedicated infrastructure
- Team collaboration features
- Advanced API (unlimited)
- Custom integrations
- Dedicated support

#### 3.2 Database Schema

```sql
-- User Management
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    oauth_provider VARCHAR(50),
    oauth_id VARCHAR(255),
    subscription_tier VARCHAR(20) DEFAULT 'free',
    credits_remaining INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Analysis Records
CREATE TABLE analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id),
    ticker VARCHAR(10) NOT NULL,
    analysis_date DATE NOT NULL,
    configuration JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    report_data JSONB,
    credits_consumed INTEGER DEFAULT 1
);

-- User API Keys
CREATE TABLE user_api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    provider VARCHAR(50),
    encrypted_key TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP
);

-- Usage Tracking
CREATE TABLE usage_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    analysis_id UUID REFERENCES analyses(id),
    action VARCHAR(50),
    credits_consumed INTEGER,
    llm_calls INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Phase 4: API Design**

#### 4.1 RESTful Endpoints

```python
# Authentication
POST   /api/auth/login
POST   /api/auth/logout
GET    /api/auth/user
PUT    /api/auth/user/settings

# Analysis Management
POST   /api/analysis/create
GET    /api/analysis/{id}
GET    /api/analysis/{id}/status
GET    /api/analysis/{id}/report
DELETE /api/analysis/{id}
GET    /api/analysis/history

# Reports
GET    /api/reports/list
GET    /api/reports/{id}
POST   /api/reports/{id}/export
POST   /api/reports/{id}/share

# User Management
GET    /api/user/subscription
PUT    /api/user/subscription
GET    /api/user/usage
POST   /api/user/api-keys
```

#### 4.2 WebSocket Events

```python
# Real-time Analysis Updates
@socketio.on('subscribe_analysis')
def handle_analysis_subscription(data):
    analysis_id = data['analysis_id']
    join_room(f"analysis_{analysis_id}")

# Events sent to client:
# - agent_status_update
# - new_message
# - report_section_complete
# - analysis_complete
# - analysis_failed
```

### **Phase 5: Implementation Timeline**

#### **Week 1-2: Foundation Setup**
- [x] Set up project structure
- [ ] Initialize Flask backend with SQLAlchemy
- [ ] Create React frontend with TypeScript
- [ ] Implement Replit Auth + Google OAuth
- [ ] Set up PostgreSQL database schema
- [ ] Create basic user registration/login flow

#### **Week 3-4: Core Backend Development**
- [ ] Build analysis API endpoints
- [ ] Integrate with existing TradingAgents framework
- [ ] Implement background job processing
- [ ] Create real-time WebSocket communication
- [ ] Set up user subscription management

#### **Week 5-6: Frontend Development**
- [ ] Create responsive dashboard layout
- [ ] Build analysis configuration wizard
- [ ] Implement real-time progress monitoring
- [ ] Create report viewing and export features
- [ ] Add user settings and API key management

#### **Week 7-8: Advanced Features**
- [ ] Implement subscription tiers and billing
- [ ] Add batch analysis capabilities
- [ ] Create notification system
- [ ] Build comprehensive API documentation
- [ ] Implement rate limiting and usage tracking

#### **Week 9-10: Testing & Deployment**
- [ ] Comprehensive testing (unit, integration, E2E)
- [ ] Performance optimization and caching
- [ ] Security audit and penetration testing
- [ ] User documentation and tutorials
- [ ] Production deployment and monitoring

### **Phase 6: Deployment Configuration**

#### 6.1 Replit Deployment Setup
```python
# .replit configuration
[deployment]
deploymentTarget = "autoscale"
run = ["sh", "-c", "cd backend && python app.py"]
build = ["sh", "-c", "cd frontend && npm run build"]

[env]
DATABASE_URL = "$DATABASE_URL"
REDIS_URL = "$REDIS_URL"
GOOGLE_OAUTH_SECRETS = "$GOOGLE_OAUTH_SECRETS"
OPENAI_API_KEY = "$OPENAI_API_KEY"
FINNHUB_API_KEY = "$FINNHUB_API_KEY"
```

#### 6.2 Environment Variables Required
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection for caching and sessions
- `GOOGLE_OAUTH_SECRETS`: Google OAuth client configuration
- `OPENAI_API_KEY`: Default OpenAI API key
- `FINNHUB_API_KEY`: Financial data API key
- `SECRET_KEY`: Flask session encryption key
- `STRIPE_SECRET_KEY`: Payment processing (Pro/Enterprise)

### **Phase 7: Success Metrics & Monitoring**

#### 7.1 Key Performance Indicators
- User registration and retention rates
- Analysis completion rates and times
- Subscription conversion rates
- API usage and error rates
- User satisfaction scores

#### 7.2 Technical Monitoring
- Application performance (response times, throughput)
- Database query performance
- Background job completion rates
- Error tracking and alerting
- Resource utilization (CPU, memory, database)

---

## 🚀 **Getting Started**

1. **Clone and Setup**: Initialize the project structure
2. **Database Setup**: Configure PostgreSQL and Redis
3. **Authentication**: Implement Replit Auth with Google OAuth
4. **Core Features**: Build analysis workflow and real-time monitoring
5. **Advanced Features**: Add subscriptions and advanced functionality
6. **Testing**: Comprehensive testing and optimization
7. **Deployment**: Production deployment and monitoring

## 📞 **Support & Documentation**

- **Development Guidelines**: Follow React and Flask best practices
- **Code Style**: Use TypeScript strict mode and Python type hints
- **Testing Strategy**: Unit tests, integration tests, and E2E testing
- **Security**: Input validation, SQL injection prevention, OWASP guidelines
- **Performance**: Caching strategies, database optimization, CDN usage

---

*This document serves as the master plan for transforming TradingAgents CLI into a comprehensive SaaS platform. Each phase builds upon the previous one, ensuring a stable and scalable foundation for growth.*