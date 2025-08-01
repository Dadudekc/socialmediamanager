#!/usr/bin/env python3
"""
Deployment script for Ultimate Follow Builder.

Automates the deployment process for different environments.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(command: str, cwd: str = None) -> bool:
    """Run a shell command and return success status."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"❌ Command failed: {command}")
            print(f"Error: {result.stderr}")
            return False
        print(f"✅ Command successful: {command}")
        return True
    except Exception as e:
        print(f"❌ Command failed: {command}")
        print(f"Error: {e}")
        return False

def check_prerequisites() -> bool:
    """Check if all prerequisites are met."""
    print("🔍 Checking prerequisites...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    
    # Check if requirements.txt exists
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found")
        return False
    
    # Check if main.py exists
    if not Path("main.py").exists():
        print("❌ main.py not found")
        return False
    
    print("✅ Prerequisites check passed")
    return True

def install_dependencies() -> bool:
    """Install Python dependencies."""
    print("📦 Installing dependencies...")
    return run_command("pip install -r requirements.txt")

def run_tests() -> bool:
    """Run the test suite."""
    print("🧪 Running tests...")
    return run_command("python -m pytest tests/ -v")

def build_package() -> bool:
    """Build the Python package."""
    print("🔨 Building package...")
    return run_command("python setup.py build")

def start_application(host: str = "0.0.0.0", port: int = 8004) -> bool:
    """Start the application."""
    print(f"🚀 Starting Ultimate Follow Builder on {host}:{port}")
    return run_command(f"python main.py --host {host} --port {port}")

def deploy_docker() -> bool:
    """Deploy using Docker."""
    print("🐳 Deploying with Docker...")
    
    # Build Docker image
    if not run_command("docker build -t ultimate-follow-builder ."):
        return False
    
    # Run Docker container
    return run_command(
        "docker run -d -p 8004:8004 --name ultimate-follow-builder ultimate-follow-builder"
    )

def deploy_production() -> bool:
    """Deploy to production environment."""
    print("🏭 Deploying to production...")
    
    # Set production environment
    os.environ["ENVIRONMENT"] = "production"
    os.environ["DEBUG"] = "False"
    
    # Install production dependencies
    if not run_command("pip install -r requirements.txt"):
        return False
    
    # Run with gunicorn for production
    return run_command(
        "gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8004"
    )

def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(description="Deploy Ultimate Follow Builder")
    parser.add_argument(
        "--environment",
        choices=["development", "production", "docker"],
        default="development",
        help="Deployment environment"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8004,
        help="Port to bind to"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running tests"
    )
    
    args = parser.parse_args()
    
    print("🚀 Ultimate Follow Builder Deployment")
    print("=" * 50)
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Run tests (unless skipped)
    if not args.skip_tests:
        if not run_tests():
            print("⚠️ Tests failed, but continuing with deployment...")
    
    # Deploy based on environment
    if args.environment == "docker":
        success = deploy_docker()
    elif args.environment == "production":
        success = deploy_production()
    else:
        success = start_application(args.host, args.port)
    
    if success:
        print("\n🎉 Deployment successful!")
        print(f"📊 Dashboard available at: http://{args.host}:{args.port}")
        print("📈 Ultimate Follow Builder is now running!")
    else:
        print("\n❌ Deployment failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 