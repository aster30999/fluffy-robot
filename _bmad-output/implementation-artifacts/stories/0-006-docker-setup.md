---
title: "US-006: Docker Setup"
story_id: "0-006-docker-setup"
epic: "Epic 0: DevOps Infrastructure"
project: "Solana Trading Bot"
created: 2026-07-02
status: "ready-for-dev"
priority: P0
dependencies: ["US-001", "US-002"]
estimate_hours: 2
type: "technical"
---

# US-006: Docker Setup

## 🎯 User Story

**As a** developer  
**I want** Docker support  
**So that** I can run the bot in a reproducible environment

## ✅ Acceptance Criteria

- [ ] `Dockerfile` in project root
- [ ] Multi-stage build (slim base image)
- [ ] All dependencies installed in container
- [ ] Environment variables for configuration
- [ ] Default to Devnet in container
- [ ] `docker-compose.yml` for development (optional)
- [ ] `.dockerignore` file
- [ ] Bot runs successfully with `docker run`

## 📋 Tasks

- [ ] Create `Dockerfile` with Python 3.12.3
- [ ] Create `.dockerignore` file
- [ ] Create `docker-compose.yml` for development
- [ ] Test Docker build locally
- [ ] Document Docker usage in README

## 🏗️ Technical Implementation

### Dockerfile Structure
- **Stage 1**: Build stage with all dependencies
- **Stage 2**: Runtime stage with slim Python 3.12.3 image
- **Working directory**: `/app`
- **Copy**: requirements.txt, src/, and other necessary files
- **Install**: pip install -r requirements.txt
- **Entry point**: Main trading bot command

### Environment Variables
- `SOLANA_RPC_URL`: Default to Devnet
- `JUPITER_API_KEY`: Optional API key
- `WALLET_PRIVATE_KEY`: For signing transactions
- `NETWORK`: devnet/mainnet (default: devnet)

### Docker Compose
- **Service**: trading-bot
- **Build**: From Dockerfile
- **Ports**: If any web interface in future
- **Volumes**: For persistent data if needed
- **Environment**: From .env file

## 📁 File Changes Required

1. `Dockerfile` - Main Docker configuration
2. `.dockerignore` - Files to exclude from Docker build context
3. `docker-compose.yml` - Development compose file (optional)
4. `README.md` - Add Docker usage section

## 🧪 Testing Strategy

### Build Test
```bash
docker build -t solana-trading-bot .
```

### Run Test
```bash
docker run --rm -it solana-trading-bot python -c "import src; print('OK')"
```

### Development Test
```bash
docker-compose up --build
```

## 📊 Success Metrics

- Dockerfile builds without errors
- All dependencies installed successfully in container
- Container starts and can import Python modules
- `docker run` executes successfully
- Docker Compose development environment works

## ⚡ Dependencies

- US-001: Project Structure Setup (must have `src/` structure)
- US-002: Environment Configuration (must have requirements.txt)
- US-005: CI/CD Pipeline Setup (for testing integration)

## 📝 Notes

- Use multi-stage build to keep final image small
- Set Python 3.12.3 as base to match local development
- Include health checks if applicable
- Consider using non-root user for security

---
*Generated for BMad workflow - Solana Trading Bot Project*