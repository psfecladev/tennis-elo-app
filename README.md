# Tennis Elo Rankings

A web application that tracks ATP tennis player Elo ratings across different court surfaces, with daily updates from Kaggle data.

## Features

- **Surface-specific Elo ratings**: Separate rankings for indoor hard, outdoor hard, clay, and grass courts
- **Daily updates**: Automated data refresh via GitHub Actions
- **Player profiles**: Detailed view with ratings across all surfaces and recent match history
- **Search**: Find players by name
- **Responsive design**: Works on desktop and mobile

## Architecture

```
tennis-elo-app/
├── backend/           # Flask API + data processing
│   ├── app/
│   │   ├── api.py           # REST endpoints
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── elo.py           # Elo calculation engine
│   │   ├── data_pipeline.py # Kaggle data download & processing
│   │   └── config.py        # Configuration
│   └── scripts/
│       └── update_ratings.py # Daily update script
├── frontend/          # SvelteKit app
│   └── src/
│       ├── lib/api.js       # API client
│       └── routes/          # Pages
└── .github/workflows/ # CI and daily update automation
```

## Tech Stack

- **Backend**: Python, Flask, SQLAlchemy, PostgreSQL
- **Frontend**: SvelteKit, deployed on Vercel
- **Data**: Kaggle ATP Tennis dataset
- **CI/CD**: GitHub Actions

## Elo Rating System

- **K-factor**: 32
- **Initial rating**: 1500
- **Minimum matches**: 5 (to appear in rankings)
- **Surface categories**: Indoor Hard, Outdoor Hard, Clay, Grass

## Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your database URL and Kaggle credentials

# Initialize database and run update
python scripts/update_ratings.py

# Run API server
python -m app.api
```

### Frontend

```bash
cd frontend
npm install

# Set environment variables
cp .env.example .env
# Edit .env with your API URL

# Development
npm run dev

# Build for production
npm run build
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Health check |
| `GET /api/surfaces` | List available surfaces |
| `GET /api/rankings/:surface` | Get rankings for a surface |
| `GET /api/players/:id` | Get player details |
| `GET /api/players?q=query` | Search players |
| `GET /api/metadata` | Get system metadata |

## Environment Variables

### Backend
- `DATABASE_URL` - PostgreSQL connection string
- `KAGGLE_USERNAME` - Kaggle username
- `KAGGLE_KEY` - Kaggle API key

### Frontend
- `VITE_API_URL` - Backend API URL

## GitHub Actions

### CI (`ci.yml`)
Runs on push/PR to main and develop:
- Backend linting (Black, isort, flake8)
- Backend tests (pytest)
- Frontend build verification
- Security scan

### Daily Update (`daily-update.yml`)
Runs daily at 6:00 AM UTC:
- Downloads latest Kaggle data
- Processes new matches
- Updates Elo ratings
- Can be triggered manually with optional full recalculation

## Required Secrets

Configure these in your GitHub repository settings:
- `DATABASE_URL` - PostgreSQL connection string
- `KAGGLE_USERNAME` - Kaggle username
- `KAGGLE_KEY` - Kaggle API key

## Data Source

[ATP Tennis 2000-2024 Daily Update](https://www.kaggle.com/datasets/dissfya/atp-tennis-2000-2024daily-update) on Kaggle

## License

MIT
