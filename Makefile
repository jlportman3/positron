.PHONY: help build up down restart logs clean test migrate seed backup restore shell-backend shell-frontend shell-db install dev prod status health check

# Variables
COMPOSE_DEV = docker-compose -f docker-compose.yml
COMPOSE_PROD = docker-compose -f docker-compose.prod.yml
BACKEND_CONTAINER = positron_backend
FRONTEND_CONTAINER = positron_frontend
POSTGRES_CONTAINER = positron_postgres
DB_NAME = positron_gam
BACKUP_DIR = ./backups

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE = \033[0;34m
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

##@ Help

help: ## Display this help message
	@echo "$(BLUE)Positron GAM Management System - Makefile Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(YELLOW)<target>$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(BLUE)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(GREEN)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development

dev: ## Start development environment
	@echo "$(GREEN)Starting development environment...$(NC)"
	$(COMPOSE_DEV) up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@echo "Frontend: http://localhost:3002"
	@echo "Backend API: http://localhost:8003"
	@echo "API Docs: http://localhost:8003/docs"

dev-build: ## Build and start development environment
	@echo "$(GREEN)Building and starting development environment...$(NC)"
	$(COMPOSE_DEV) up -d --build
	@echo "$(GREEN)✓ Services built and started$(NC)"

stop: ## Stop development environment
	@echo "$(YELLOW)Stopping development environment...$(NC)"
	$(COMPOSE_DEV) stop
	@echo "$(GREEN)✓ Services stopped$(NC)"

down: ## Stop and remove development containers
	@echo "$(YELLOW)Stopping and removing containers...$(NC)"
	$(COMPOSE_DEV) down
	@echo "$(GREEN)✓ Containers removed$(NC)"

restart: ## Restart development environment
	@echo "$(YELLOW)Restarting services...$(NC)"
	$(COMPOSE_DEV) restart
	@echo "$(GREEN)✓ Services restarted$(NC)"

logs: ## Show logs from all services
	$(COMPOSE_DEV) logs -f

logs-backend: ## Show backend logs
	$(COMPOSE_DEV) logs -f $(BACKEND_CONTAINER)

logs-frontend: ## Show frontend logs
	$(COMPOSE_DEV) logs -f $(FRONTEND_CONTAINER)

logs-db: ## Show database logs
	$(COMPOSE_DEV) logs -f $(POSTGRES_CONTAINER)

status: ## Show status of all services
	@echo "$(BLUE)Service Status:$(NC)"
	$(COMPOSE_DEV) ps

##@ Database

migrate: ## Run database migrations
	@echo "$(GREEN)Running database migrations...$(NC)"
	$(COMPOSE_DEV) exec $(BACKEND_CONTAINER) alembic upgrade head
	@echo "$(GREEN)✓ Migrations completed$(NC)"

migrate-create: ## Create a new migration (use MSG="description")
	@echo "$(GREEN)Creating new migration...$(NC)"
	$(COMPOSE_DEV) exec $(BACKEND_CONTAINER) alembic revision --autogenerate -m "$(MSG)"
	@echo "$(GREEN)✓ Migration created$(NC)"

migrate-rollback: ## Rollback last migration
	@echo "$(YELLOW)Rolling back last migration...$(NC)"
	$(COMPOSE_DEV) exec $(BACKEND_CONTAINER) alembic downgrade -1
	@echo "$(GREEN)✓ Rollback completed$(NC)"

migrate-history: ## Show migration history
	$(COMPOSE_DEV) exec $(BACKEND_CONTAINER) alembic history

seed: ## Seed database with sample data
	@echo "$(GREEN)Seeding database...$(NC)"
	$(COMPOSE_DEV) exec $(BACKEND_CONTAINER) python -m app.scripts.seed_data
	@echo "$(GREEN)✓ Database seeded$(NC)"

backup: ## Backup database
	@echo "$(GREEN)Backing up database...$(NC)"
	@mkdir -p $(BACKUP_DIR)
	$(COMPOSE_DEV) exec -T $(POSTGRES_CONTAINER) pg_dump -U postgres $(DB_NAME) > $(BACKUP_DIR)/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✓ Backup created in $(BACKUP_DIR)$(NC)"

restore: ## Restore database from latest backup (use FILE=path/to/backup.sql)
	@echo "$(YELLOW)Restoring database from $(FILE)...$(NC)"
	@cat $(FILE) | $(COMPOSE_DEV) exec -T $(POSTGRES_CONTAINER) psql -U postgres $(DB_NAME)
	@echo "$(GREEN)✓ Database restored$(NC)"

db-shell: ## Access PostgreSQL shell
	$(COMPOSE_DEV) exec $(POSTGRES_CONTAINER) psql -U postgres -d $(DB_NAME)

db-reset: ## Reset database (WARNING: deletes all data)
	@echo "$(RED)WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(YELLOW)Resetting database...$(NC)"; \
		$(COMPOSE_DEV) down -v; \
		$(COMPOSE_DEV) up -d $(POSTGRES_CONTAINER); \
		sleep 5; \
		$(COMPOSE_DEV) up -d; \
		sleep 5; \
		make migrate; \
		echo "$(GREEN)✓ Database reset completed$(NC)"; \
	fi

##@ Testing

test: ## Run backend tests
	@echo "$(GREEN)Running tests...$(NC)"
	$(COMPOSE_DEV) exec $(BACKEND_CONTAINER) pytest
	@echo "$(GREEN)✓ Tests completed$(NC)"

test-cov: ## Run tests with coverage
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	$(COMPOSE_DEV) exec $(BACKEND_CONTAINER) pytest --cov=app --cov-report=html
	@echo "$(GREEN)✓ Coverage report generated$(NC)"

test-frontend: ## Run frontend tests
	@echo "$(GREEN)Running frontend tests...$(NC)"
	$(COMPOSE_DEV) exec $(FRONTEND_CONTAINER) npm test
	@echo "$(GREEN)✓ Frontend tests completed$(NC)"

lint: ## Lint backend code
	@echo "$(GREEN)Linting backend code...$(NC)"
	$(COMPOSE_DEV) exec $(BACKEND_CONTAINER) flake8 app/
	@echo "$(GREEN)✓ Linting completed$(NC)"

lint-frontend: ## Lint frontend code
	@echo "$(GREEN)Linting frontend code...$(NC)"
	$(COMPOSE_DEV) exec $(FRONTEND_CONTAINER) npm run lint
	@echo "$(GREEN)✓ Frontend linting completed$(NC)"

##@ Shell Access

shell-backend: ## Access backend container shell
	$(COMPOSE_DEV) exec $(BACKEND_CONTAINER) bash

shell-frontend: ## Access frontend container shell
	$(COMPOSE_DEV) exec $(FRONTEND_CONTAINER) sh

shell-db: ## Access database container shell
	$(COMPOSE_DEV) exec $(POSTGRES_CONTAINER) bash

##@ Installation & Setup

install: ## Install dependencies (backend and frontend)
	@echo "$(GREEN)Installing dependencies...$(NC)"
	$(COMPOSE_DEV) exec $(BACKEND_CONTAINER) pip install -r requirements.txt
	$(COMPOSE_DEV) exec $(FRONTEND_CONTAINER) npm install
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

setup: ## Initial setup (build, migrate, seed)
	@echo "$(GREEN)Running initial setup...$(NC)"
	make dev-build
	@sleep 10
	make migrate
	@echo "$(GREEN)✓ Setup completed$(NC)"
	@echo ""
	@echo "$(BLUE)Access your application:$(NC)"
	@echo "  Frontend: http://localhost:3002"
	@echo "  Backend:  http://localhost:8003"
	@echo "  API Docs: http://localhost:8003/docs"

verify: ## Verify setup
	@echo "$(GREEN)Verifying setup...$(NC)"
	@bash verify-setup.sh

check: ## Health check all services
	@echo "$(BLUE)Checking service health...$(NC)"
	@curl -s http://localhost:8003/health | grep -q "healthy" && echo "$(GREEN)✓ Backend: Healthy$(NC)" || echo "$(RED)✗ Backend: Unhealthy$(NC)"
	@curl -s http://localhost:3002 > /dev/null && echo "$(GREEN)✓ Frontend: Healthy$(NC)" || echo "$(RED)✗ Frontend: Unhealthy$(NC)"
	@docker ps | grep -q $(POSTGRES_CONTAINER) && echo "$(GREEN)✓ Database: Running$(NC)" || echo "$(RED)✗ Database: Not Running$(NC)"

##@ Production

prod: ## Start production environment
	@echo "$(GREEN)Starting production environment...$(NC)"
	$(COMPOSE_PROD) up -d
	@echo "$(GREEN)✓ Production services started$(NC)"

prod-build: ## Build production environment
	@echo "$(GREEN)Building production environment...$(NC)"
	$(COMPOSE_PROD) build
	@echo "$(GREEN)✓ Production build completed$(NC)"

prod-deploy: ## Deploy to production (build, up, migrate)
	@echo "$(GREEN)Deploying to production...$(NC)"
	$(COMPOSE_PROD) build
	$(COMPOSE_PROD) up -d
	@sleep 10
	$(COMPOSE_PROD) exec backend alembic upgrade head
	@echo "$(GREEN)✓ Production deployment completed$(NC)"

prod-down: ## Stop production environment
	@echo "$(YELLOW)Stopping production environment...$(NC)"
	$(COMPOSE_PROD) down
	@echo "$(GREEN)✓ Production services stopped$(NC)"

prod-logs: ## Show production logs
	$(COMPOSE_PROD) logs -f

##@ Maintenance

clean: ## Clean up containers, volumes, and images
	@echo "$(YELLOW)Cleaning up...$(NC)"
	$(COMPOSE_DEV) down -v
	docker system prune -f
	@echo "$(GREEN)✓ Cleanup completed$(NC)"

clean-all: ## Clean everything including images
	@echo "$(RED)WARNING: This will remove all containers, volumes, and images!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		$(COMPOSE_DEV) down -v --rmi all; \
		docker system prune -af; \
		echo "$(GREEN)✓ Full cleanup completed$(NC)"; \
	fi

update: ## Update and restart services
	@echo "$(GREEN)Updating services...$(NC)"
	git pull
	$(COMPOSE_DEV) down
	$(COMPOSE_DEV) up -d --build
	make migrate
	@echo "$(GREEN)✓ Update completed$(NC)"

rebuild: ## Rebuild all containers
	@echo "$(GREEN)Rebuilding containers...$(NC)"
	$(COMPOSE_DEV) down
	$(COMPOSE_DEV) build --no-cache
	$(COMPOSE_DEV) up -d
	@echo "$(GREEN)✓ Rebuild completed$(NC)"

##@ Quick Commands

quick-start: setup ## Alias for setup
	@echo "$(GREEN)Quick start completed!$(NC)"

quick-stop: down ## Alias for down
	@echo "$(GREEN)Stopped!$(NC)"

quick-restart: ## Quick restart (down, up, migrate)
	@echo "$(YELLOW)Quick restarting...$(NC)"
	make down
	make dev
	@sleep 5
	make migrate
	@echo "$(GREEN)✓ Quick restart completed$(NC)"

##@ Docker Operations

ps: ## Show running containers
	docker ps --filter "name=positron"

images: ## Show positron images
	docker images | grep positron

volumes: ## Show positron volumes
	docker volume ls | grep positron

stats: ## Show container resource usage
	docker stats --no-stream $$(docker ps --filter "name=positron" -q)

prune: ## Remove unused Docker resources
	docker system prune -f

##@ Utility

env: ## Show environment configuration
	@echo "$(BLUE)Environment Configuration:$(NC)"
	@grep -v '^#' .env | grep -v '^$$'

ports: ## Show port usage
	@echo "$(BLUE)Port Usage:$(NC)"
	@echo "PostgreSQL: 5436"
	@echo "Redis:      6380"
	@echo "Backend:    8001"
	@echo "Frontend:   3001"
	@lsof -i :5436 -i :6380 -i :8003 -i :3002 2>/dev/null || echo "No ports in use"

docs: ## Open API documentation in browser
	@echo "$(GREEN)Opening API documentation...$(NC)"
	@open http://localhost:8003/docs 2>/dev/null || xdg-open http://localhost:8003/docs 2>/dev/null || echo "Open http://localhost:8003/docs in your browser"

frontend: ## Open frontend in browser
	@echo "$(GREEN)Opening frontend...$(NC)"
	@open http://localhost:3002 2>/dev/null || xdg-open http://localhost:3002 2>/dev/null || echo "Open http://localhost:3002 in your browser"

##@ Advanced

tail: ## Tail logs from all services (use SVC=service_name for specific service)
ifdef SVC
	$(COMPOSE_DEV) logs -f --tail=100 $(SVC)
else
	$(COMPOSE_DEV) logs -f --tail=100
endif

exec: ## Execute command in backend (use CMD="command")
	$(COMPOSE_DEV) exec $(BACKEND_CONTAINER) $(CMD)

scale: ## Scale backend services (use NUM=number)
	@echo "$(GREEN)Scaling backend to $(NUM) instances...$(NC)"
	$(COMPOSE_DEV) up -d --scale $(BACKEND_CONTAINER)=$(NUM)
	@echo "$(GREEN)✓ Scaled to $(NUM) instances$(NC)"

version: ## Show version information
	@echo "$(BLUE)Positron GAM Management System$(NC)"
	@echo "Version: 1.0.0"
	@echo ""
	@echo "Components:"
	@$(COMPOSE_DEV) exec $(BACKEND_CONTAINER) python --version 2>/dev/null || echo "Backend: Not running"
	@$(COMPOSE_DEV) exec $(FRONTEND_CONTAINER) node --version 2>/dev/null || echo "Frontend: Not running"
	@$(COMPOSE_DEV) exec $(POSTGRES_CONTAINER) psql --version 2>/dev/null || echo "PostgreSQL: Not running"

info: ## Show system information
	@echo "$(BLUE)System Information$(NC)"
	@echo "Docker version:"
	@docker --version
	@echo ""
	@echo "Docker Compose version:"
	@docker-compose --version
	@echo ""
	@echo "Disk usage:"
	@docker system df
	@echo ""
	@make status
