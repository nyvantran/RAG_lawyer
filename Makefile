.PHONY: up up-gpu down restart restart-gpu build build-gpu logs logs-backend logs-frontend prepare-qdrant prepare-qdrant-clean help

# Tự động dò tìm Python của môi trường conda raglawyer trên Windows, fallback về python mặc định nếu không tìm thấy
ifeq ($(OS),Windows_NT)
    CONDA_PYTHON = D:\Users\tonda\anaconda3\envs\raglawyer\python.exe
    PYTHON = $(if $(wildcard $(CONDA_PYTHON)),$(CONDA_PYTHON),python)
else
    PYTHON = python3
endif

# Biến cấu hình
QDRANT_URL = http://qdrant:6333
COLLECTION_NAME = RAG_lawyer
DATA_DIR = data/LuatLaoDong2025_temp

help:
	@echo "========================================================================"
	@echo "                     RAG LAWYER DEPLOYMENT MAKEFILE                     "
	@echo "========================================================================"
	@echo "Available commands:"
	@echo "  make up                  - Start the system in CPU mode (background)"
	@echo "  make up-gpu              - Start the system in GPU/CUDA mode (background)"
	@echo "  make down                - Stop and remove all containers"
	@echo "  make restart             - Restart the system in CPU mode"
	@echo "  make restart-gpu         - Restart the system in GPU/CUDA mode"
	@echo "  make build               - Rebuild Docker images for CPU mode"
	@echo "  make build-gpu           - Rebuild Docker images for GPU/CUDA mode"
	@echo "  make logs                - View real-time logs for all containers"
	@echo "  make logs-backend        - View real-time logs for Backend container"
	@echo "  make logs-frontend       - View real-time logs for Frontend container"
	@echo "  make prepare-qdrant      - Run script to prepare Qdrant vectorstore and upsert data"
	@echo "  make prepare-qdrant-clean- Run script to recreate Qdrant vectorstore and upsert data"
	@echo "========================================================================"

# --- DOCKER COMPOSE COMMANDS ---

up:
	docker compose up -d
	@echo "System is starting in CPU mode at http://localhost:3000 (Frontend) and http://localhost:8000 (Backend)"

up-gpu:
	docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
	@echo "System is starting in GPU (CUDA) mode at http://localhost:3000 (Frontend) and http://localhost:8000 (Backend)"

down:
	docker compose -f docker-compose.yml -f docker-compose.gpu.yml down
	@echo "Stopped and removed all containers."

restart: down up

restart-gpu: down up-gpu

build:
	docker compose build --no-cache

build-gpu:
	docker compose -f docker-compose.yml -f docker-compose.gpu.yml build --no-cache

logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-frontend:
	docker compose logs -f frontend

# --- DATA PREPARATION COMMANDS ---

prepare-qdrant:
	docker compose exec backend python scripts/prepare_qdrant.py --qdrant-url $(QDRANT_URL) --collection $(COLLECTION_NAME) --data-dir $(DATA_DIR)

prepare-qdrant-clean:
	docker compose exec backend python scripts/prepare_qdrant.py --qdrant-url $(QDRANT_URL) --collection $(COLLECTION_NAME) --data-dir $(DATA_DIR) --recreate
