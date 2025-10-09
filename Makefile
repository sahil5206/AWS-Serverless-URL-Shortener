# Makefile for AWS Serverless URL Shortener

.PHONY: help install test lint format clean build deploy-local deploy-dev deploy-prod terraform-plan terraform-apply

# Default target
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	pip install -r requirements.txt

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=lambda --cov-report=html --cov-report=term-missing

lint: ## Run linting
	flake8 lambda/ tests/
	isort --check-only lambda/ tests/
	black --check lambda/ tests/
	mypy lambda/

format: ## Format code
	isort lambda/ tests/
	black lambda/ tests/

clean: ## Clean build artifacts
	rm -rf .aws-sam/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: ## Build SAM application
	sam build

deploy-local: ## Deploy locally for testing
	sam local start-api

deploy-dev: ## Deploy to development environment
	cd terraform && terraform apply -var="environment=dev" -auto-approve
	sam build
	sam deploy --config-env dev

deploy-prod: ## Deploy to production environment
	cd terraform && terraform apply -var="environment=prod" -auto-approve
	sam build
	sam deploy --config-env production

terraform-plan: ## Plan Terraform changes
	cd terraform && terraform plan

terraform-apply: ## Apply Terraform changes
	cd terraform && terraform apply

terraform-init: ## Initialize Terraform
	cd terraform && terraform init

security-scan: ## Run security scan
	bandit -r lambda/

all-checks: lint test security-scan ## Run all quality checks

dev-setup: install terraform-init ## Set up development environment
	@echo "Development environment setup complete!"
	@echo "Run 'make deploy-dev' to deploy to development"
