import os
import logging
import subprocess
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from project_config import config
from setup_logging import setup_logging

logger = setup_logging("cloud_deployment", log_dir=config.LOG_DIR)

class CloudDeployment:
    """Handles cloud deployment and infrastructure management."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.deployment_dir = self.project_root / "deployment"
        self.deployment_dir.mkdir(exist_ok=True)
        
        # Docker configuration
        self.dockerfile_path = self.deployment_dir / "Dockerfile"
        self.docker_compose_path = self.deployment_dir / "docker-compose.yml"
        
        # Kubernetes configuration
        self.k8s_dir = self.deployment_dir / "kubernetes"
        self.k8s_dir.mkdir(exist_ok=True)
        
        # Terraform configuration
        self.terraform_dir = self.deployment_dir / "terraform"
        self.terraform_dir.mkdir(exist_ok=True)
        
        logger.info("✅ Cloud deployment system initialized")
    
    def create_dockerfile(self) -> str:
        """Create Dockerfile for containerization."""
        dockerfile_content = """# Multi-stage build for Social Media Sentiment Analysis
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    wget \\
    gnupg \\
    unzip \\
    && rm -rf /var/lib/apt/lists/*

# Install Chrome and ChromeDriver
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \\
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \\
    && apt-get update \\
    && apt-get install -y google-chrome-stable \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/models /app/chrome_profile

# Set environment variables
ENV PYTHONPATH=/app
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# Expose ports
EXPOSE 8000 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Default command
CMD ["python", "main.py"]
"""
        
        with open(self.dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
        
        logger.info(f"✅ Dockerfile created at {self.dockerfile_path}")
        return str(self.dockerfile_path)
    
    def create_docker_compose(self) -> str:
        """Create docker-compose.yml for local development and testing."""
        compose_content = """version: '3.8'

services:
  sentiment-analysis:
    build: .
    container_name: sentiment-analysis-app
    ports:
      - "8000:8000"
      - "8080:8080"
    environment:
      - MYSQL_DB_HOST=mysql
      - MYSQL_DB_NAME=sentiment_db
      - MYSQL_DB_USER=sentiment_user
      - MYSQL_DB_PASSWORD=sentiment_password
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - DISCORD_CHANNEL_ID=${DISCORD_CHANNEL_ID}
      - ALPACA_API_KEY=${ALPACA_API_KEY}
      - ALPACA_SECRET_KEY=${ALPACA_SECRET_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./models:/app/models
      - ./chrome_profile:/app/chrome_profile
    depends_on:
      - mysql
      - redis
    restart: unless-stopped
    networks:
      - sentiment-network

  mysql:
    image: mysql:8.0
    container_name: sentiment-mysql
    environment:
      - MYSQL_ROOT_PASSWORD=root_password
      - MYSQL_DATABASE=sentiment_db
      - MYSQL_USER=sentiment_user
      - MYSQL_PASSWORD=sentiment_password
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./deployment/mysql/init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped
    networks:
      - sentiment-network

  redis:
    image: redis:7-alpine
    container_name: sentiment-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - sentiment-network

  nginx:
    image: nginx:alpine
    container_name: sentiment-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deployment/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./deployment/nginx/ssl:/etc/nginx/ssl
    depends_on:
      - sentiment-analysis
    restart: unless-stopped
    networks:
      - sentiment-network

volumes:
  mysql_data:
  redis_data:

networks:
  sentiment-network:
    driver: bridge
"""
        
        with open(self.docker_compose_path, 'w') as f:
            f.write(compose_content)
        
        logger.info(f"✅ Docker Compose file created at {self.docker_compose_path}")
        return str(self.docker_compose_path)
    
    def create_kubernetes_configs(self) -> Dict[str, str]:
        """Create Kubernetes configuration files."""
        configs = {}
        
        # Namespace
        namespace_content = """apiVersion: v1
kind: Namespace
metadata:
  name: sentiment-analysis
  labels:
    name: sentiment-analysis
"""
        namespace_path = self.k8s_dir / "namespace.yml"
        with open(namespace_path, 'w') as f:
            f.write(namespace_content)
        configs["namespace"] = str(namespace_path)
        
        # ConfigMap
        configmap_content = """apiVersion: v1
kind: ConfigMap
metadata:
  name: sentiment-config
  namespace: sentiment-analysis
data:
  LOG_LEVEL: "INFO"
  CHROME_PROFILE_PATH: "/app/chrome_profile"
  COOKIE_STORAGE_PATH: "/app/cookies"
  MAX_LOGIN_ATTEMPTS: "3"
  LOGIN_WAIT_TIME: "5"
  CAPTCHA_WAIT_TIME: "10"
  DEBUG_MODE: "false"
"""
        configmap_path = self.k8s_dir / "configmap.yml"
        with open(configmap_path, 'w') as f:
            f.write(configmap_content)
        configs["configmap"] = str(configmap_path)
        
        # Secret
        secret_content = """apiVersion: v1
kind: Secret
metadata:
  name: sentiment-secrets
  namespace: sentiment-analysis
type: Opaque
data:
  DISCORD_TOKEN: <base64-encoded-token>
  DISCORD_CHANNEL_ID: <base64-encoded-channel-id>
  ALPACA_API_KEY: <base64-encoded-api-key>
  ALPACA_SECRET_KEY: <base64-encoded-secret-key>
  MYSQL_DB_PASSWORD: <base64-encoded-password>
"""
        secret_path = self.k8s_dir / "secret.yml"
        with open(secret_path, 'w') as f:
            f.write(secret_content)
        configs["secret"] = str(secret_path)
        
        # Deployment
        deployment_content = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: sentiment-analysis
  namespace: sentiment-analysis
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sentiment-analysis
  template:
    metadata:
      labels:
        app: sentiment-analysis
    spec:
      containers:
      - name: sentiment-analysis
        image: sentiment-analysis:latest
        ports:
        - containerPort: 8000
        - containerPort: 8080
        env:
        - name: MYSQL_DB_HOST
          value: "sentiment-mysql"
        - name: MYSQL_DB_NAME
          value: "sentiment_db"
        - name: MYSQL_DB_USER
          value: "sentiment_user"
        - name: MYSQL_DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: sentiment-secrets
              key: MYSQL_DB_PASSWORD
        - name: DISCORD_TOKEN
          valueFrom:
            secretKeyRef:
              name: sentiment-secrets
              key: DISCORD_TOKEN
        - name: DISCORD_CHANNEL_ID
          valueFrom:
            secretKeyRef:
              name: sentiment-secrets
              key: DISCORD_CHANNEL_ID
        - name: ALPACA_API_KEY
          valueFrom:
            secretKeyRef:
              name: sentiment-secrets
              key: ALPACA_API_KEY
        - name: ALPACA_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: sentiment-secrets
              key: ALPACA_SECRET_KEY
        envFrom:
        - configMapRef:
            name: sentiment-config
        volumeMounts:
        - name: data-volume
          mountPath: /app/data
        - name: logs-volume
          mountPath: /app/logs
        - name: models-volume
          mountPath: /app/models
        - name: chrome-profile
          mountPath: /app/chrome_profile
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: sentiment-data-pvc
      - name: logs-volume
        persistentVolumeClaim:
          claimName: sentiment-logs-pvc
      - name: models-volume
        persistentVolumeClaim:
          claimName: sentiment-models-pvc
      - name: chrome-profile
        emptyDir: {}
"""
        deployment_path = self.k8s_dir / "deployment.yml"
        with open(deployment_path, 'w') as f:
            f.write(deployment_content)
        configs["deployment"] = str(deployment_path)
        
        # Service
        service_content = """apiVersion: v1
kind: Service
metadata:
  name: sentiment-analysis-service
  namespace: sentiment-analysis
spec:
  selector:
    app: sentiment-analysis
  ports:
  - name: http
    port: 80
    targetPort: 8000
  - name: dashboard
    port: 8080
    targetPort: 8080
  type: ClusterIP
"""
        service_path = self.k8s_dir / "service.yml"
        with open(service_path, 'w') as f:
            f.write(service_content)
        configs["service"] = str(service_path)
        
        # Ingress
        ingress_content = """apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: sentiment-analysis-ingress
  namespace: sentiment-analysis
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  rules:
  - host: sentiment-analysis.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: sentiment-analysis-service
            port:
              number: 80
      - path: /dashboard
        pathType: Prefix
        backend:
          service:
            name: sentiment-analysis-service
            port:
              number: 8080
  tls:
  - hosts:
    - sentiment-analysis.example.com
    secretName: sentiment-tls-secret
"""
        ingress_path = self.k8s_dir / "ingress.yml"
        with open(ingress_path, 'w') as f:
            f.write(ingress_content)
        configs["ingress"] = str(ingress_path)
        
        # Persistent Volume Claims
        pvc_content = """apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: sentiment-data-pvc
  namespace: sentiment-analysis
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: sentiment-logs-pvc
  namespace: sentiment-analysis
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: sentiment-models-pvc
  namespace: sentiment-analysis
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 2Gi
"""
        pvc_path = self.k8s_dir / "pvc.yml"
        with open(pvc_path, 'w') as f:
            f.write(pvc_content)
        configs["pvc"] = str(pvc_path)
        
        logger.info(f"✅ Kubernetes configs created in {self.k8s_dir}")
        return configs
    
    def create_terraform_config(self) -> Dict[str, str]:
        """Create Terraform configuration for infrastructure."""
        configs = {}
        
        # Main Terraform configuration
        main_tf_content = """terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC and Networking
resource "aws_vpc" "sentiment_vpc" {
  cidr_block = "10.0.0.0/16"
  
  tags = {
    Name = "sentiment-analysis-vpc"
    Environment = var.environment
  }
}

resource "aws_subnet" "public" {
  vpc_id     = aws_vpc.sentiment_vpc.id
  cidr_block = "10.0.1.0/24"
  
  tags = {
    Name = "sentiment-public-subnet"
  }
}

resource "aws_subnet" "private" {
  vpc_id     = aws_vpc.sentiment_vpc.id
  cidr_block = "10.0.2.0/24"
  
  tags = {
    Name = "sentiment-private-subnet"
  }
}

# EKS Cluster
resource "aws_eks_cluster" "sentiment_cluster" {
  name     = "sentiment-analysis-cluster"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = "1.24"
  
  vpc_config {
    subnet_ids = [aws_subnet.public.id, aws_subnet.private.id]
  }
  
  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy
  ]
}

# EKS Node Group
resource "aws_eks_node_group" "sentiment_nodes" {
  cluster_name    = aws_eks_cluster.sentiment_cluster.name
  node_group_name = "sentiment-node-group"
  node_role_arn   = aws_iam_role.eks_node_group.arn
  subnet_ids      = [aws_subnet.private.id]
  
  scaling_config {
    desired_size = 2
    max_size     = 4
    min_size     = 1
  }
  
  instance_types = ["t3.medium"]
  
  depends_on = [
    aws_iam_role_policy_attachment.eks_node_group_policy
  ]
}

# RDS Database
resource "aws_db_instance" "sentiment_db" {
  identifier = "sentiment-analysis-db"
  
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = "db.t3.micro"
  
  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp2"
  
  db_name  = "sentiment_db"
  username = "sentiment_user"
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.sentiment.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  skip_final_snapshot = true
  
  tags = {
    Environment = var.environment
  }
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "sentiment_redis" {
  cluster_id           = "sentiment-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis6.x"
  port                 = 6379
  
  security_group_ids = [aws_security_group.redis.id]
  subnet_group_name  = aws_elasticache_subnet_group.sentiment.name
}

# Application Load Balancer
resource "aws_lb" "sentiment_alb" {
  name               = "sentiment-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = [aws_subnet.public.id]
  
  tags = {
    Environment = var.environment
  }
}

# Security Groups
resource "aws_security_group" "alb" {
  name_prefix = "sentiment-alb"
  vpc_id      = aws_vpc.sentiment_vpc.id
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "rds" {
  name_prefix = "sentiment-rds"
  vpc_id      = aws_vpc.sentiment_vpc.id
  
  ingress {
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.eks.id]
  }
}

resource "aws_security_group" "redis" {
  name_prefix = "sentiment-redis"
  vpc_id      = aws_vpc.sentiment_vpc.id
  
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.eks.id]
  }
}

resource "aws_security_group" "eks" {
  name_prefix = "sentiment-eks"
  vpc_id      = aws_vpc.sentiment_vpc.id
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
"""
        main_tf_path = self.terraform_dir / "main.tf"
        with open(main_tf_path, 'w') as f:
            f.write(main_tf_content)
        configs["main"] = str(main_tf_path)
        
        # Variables
        variables_content = """variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = "sentiment-analysis.example.com"
}
"""
        variables_path = self.terraform_dir / "variables.tf"
        with open(variables_path, 'w') as f:
            f.write(variables_content)
        configs["variables"] = str(variables_path)
        
        # Outputs
        outputs_content = """output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = aws_eks_cluster.sentiment_cluster.endpoint
}

output "cluster_security_group_id" {
  description = "Security group ID attached to the EKS cluster"
  value       = aws_eks_cluster.sentiment_cluster.vpc_config[0].cluster_security_group_id
}

output "cluster_iam_role_name" {
  description = "IAM role name associated with EKS cluster"
  value       = aws_eks_cluster.sentiment_cluster.role_arn
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = aws_eks_cluster.sentiment_cluster.certificate_authority[0].data
}

output "db_endpoint" {
  description = "RDS database endpoint"
  value       = aws_db_instance.sentiment_db.endpoint
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = aws_elasticache_cluster.sentiment_redis.cache_nodes[0].address
}

output "alb_dns_name" {
  description = "Application Load Balancer DNS name"
  value       = aws_lb.sentiment_alb.dns_name
}
"""
        outputs_path = self.terraform_dir / "outputs.tf"
        with open(outputs_path, 'w') as f:
            f.write(outputs_content)
        configs["outputs"] = str(outputs_path)
        
        logger.info(f"✅ Terraform configs created in {self.terraform_dir}")
        return configs
    
    def create_github_actions(self) -> str:
        """Create GitHub Actions workflow for CI/CD."""
        workflows_dir = self.project_root / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        
        workflow_content = """name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest --cov=./ --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2
    
    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        file: ./deployment/Dockerfile
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: us-west-2
    
    - name: Update kubeconfig
      run: aws eks update-kubeconfig --name sentiment-analysis-cluster --region us-west-2
    
    - name: Deploy to EKS
      run: |
        kubectl apply -f deployment/kubernetes/
        kubectl set image deployment/sentiment-analysis sentiment-analysis=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
"""
        
        workflow_path = workflows_dir / "ci-cd.yml"
        with open(workflow_path, 'w') as f:
            f.write(workflow_content)
        
        logger.info(f"✅ GitHub Actions workflow created at {workflow_path}")
        return str(workflow_path)
    
    def build_docker_image(self, tag: str = "latest") -> bool:
        """Build Docker image."""
        try:
            cmd = [
                "docker", "build",
                "-f", str(self.dockerfile_path),
                "-t", f"sentiment-analysis:{tag}",
                "."
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                logger.info(f"✅ Docker image built successfully: sentiment-analysis:{tag}")
                return True
            else:
                logger.error(f"❌ Docker build failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error building Docker image: {e}")
            return False
    
    def deploy_to_kubernetes(self, namespace: str = "sentiment-analysis") -> bool:
        """Deploy to Kubernetes cluster."""
        try:
            # Apply namespace first
            namespace_cmd = ["kubectl", "apply", "-f", str(self.k8s_dir / "namespace.yml")]
            subprocess.run(namespace_cmd, check=True)
            
            # Apply all other resources
            for config_file in self.k8s_dir.glob("*.yml"):
                if config_file.name != "namespace.yml":
                    cmd = ["kubectl", "apply", "-f", str(config_file)]
                    subprocess.run(cmd, check=True)
            
            logger.info(f"✅ Successfully deployed to Kubernetes namespace: {namespace}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Kubernetes deployment failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error deploying to Kubernetes: {e}")
            return False
    
    def create_deployment_script(self) -> str:
        """Create deployment script."""
        script_content = """#!/bin/bash

# Social Media Sentiment Analysis Deployment Script
set -e

echo "🚀 Starting deployment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build Docker image
echo "📦 Building Docker image..."
docker build -f deployment/Dockerfile -t sentiment-analysis:latest .

# Run with docker-compose for local testing
echo "🐳 Starting services with docker-compose..."
docker-compose -f deployment/docker-compose.yml up -d

echo "✅ Deployment completed successfully!"
echo "📊 Dashboard available at: http://localhost:8000"
echo "📈 Application logs: docker-compose logs -f sentiment-analysis"
"""
        
        script_path = self.deployment_dir / "deploy.sh"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        os.chmod(script_path, 0o755)
        
        logger.info(f"✅ Deployment script created at {script_path}")
        return str(script_path)

if __name__ == "__main__":
    # Example usage
    deployment = CloudDeployment()
    
    # Create all deployment configurations
    dockerfile_path = deployment.create_dockerfile()
    compose_path = deployment.create_docker_compose()
    k8s_configs = deployment.create_kubernetes_configs()
    terraform_configs = deployment.create_terraform_config()
    github_actions_path = deployment.create_github_actions()
    deploy_script_path = deployment.create_deployment_script()
    
    print(f"✅ All deployment configurations created:")
    print(f"  - Dockerfile: {dockerfile_path}")
    print(f"  - Docker Compose: {compose_path}")
    print(f"  - Kubernetes configs: {len(k8s_configs)} files")
    print(f"  - Terraform configs: {len(terraform_configs)} files")
    print(f"  - GitHub Actions: {github_actions_path}")
    print(f"  - Deployment script: {deploy_script_path}") 