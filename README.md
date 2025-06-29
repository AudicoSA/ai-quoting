# Audico AI Audio Solutions Quotation System

## Quick Start

1. Extract the project files
2. Configure environment variables
3. Run with Docker: `docker-compose up`
4. Access at http://localhost:3000

## Features

- Solutions-focused AI conversations
- LangChain integration for intelligent recommendations
- South African Rands pricing
- Professional PDF quote generation
- SQLantern database integration
- Real-time quote building

## Environment Setup

### Backend (.env)
```
DATABASE_URL=postgresql://audico_admin:AudicoAI2024!@localhost:5432/audico_ai_db
OPENAI_API_KEY=your_openai_api_key_here
JWT_SECRET=audico_jwt_secret_2024_secure_key
SQLANTERN_API_KEY=sqlantern_key_audico_2024
REDIS_URL=redis://localhost:6379
```

### Frontend (.env)
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws
```

## Your Database Integration

Use your existing audicoonline.co.za database:
- Host: dedi159.cpt4.host-h.net
- Database: audicdmyde_db__359
- Username: audicdmyde_314
- Password: 4hG4xcGS3tSgX76o5FSv

## Development

The project includes complete backend and frontend with:
- FastAPI + LangChain backend
- React + Material-UI frontend
- PostgreSQL database
- Docker containerization
- Professional PDF generation

Start development immediately with the provided structure!
