#!/usr/bin/env python3
"""
Waardhaven AutoIndex - Automated Deployment Script
Handles zero-cost deployment to multiple providers
"""

import os
import sys
import subprocess
import argparse
import json
import time
from typing import Dict, List, Optional
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeploymentManager:
    """Manages deployment to various providers."""
    
    def __init__(self, target: str = 'production', dry_run: bool = False):
        self.target = target
        self.dry_run = dry_run
        self.root_dir = Path(__file__).parent
        self.api_dir = self.root_dir / 'apps' / 'api'
        self.web_dir = self.root_dir / 'apps' / 'web'
        
    def run_command(self, command: str, cwd: Optional[Path] = None) -> bool:
        """Execute a shell command."""
        
        if self.dry_run:
            logger.info(f"DRY RUN: Would execute: {command}")
            return True
            
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd or self.root_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Command failed: {command}")
                logger.error(f"Error: {result.stderr}")
                return False
                
            if result.stdout:
                logger.debug(result.stdout)
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute command: {e}")
            return False
            
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are installed."""
        
        logger.info("Checking prerequisites...")
        
        requirements = {
            'git': 'git --version',
            'node': 'node --version',
            'npm': 'npm --version',
            'python': 'python --version',
            'pip': 'pip --version'
        }
        
        for tool, command in requirements.items():
            if not self.run_command(command):
                logger.error(f"{tool} is not installed")
                return False
                
        # Check for CLI tools
        optional_tools = {
            'vercel': 'npm install -g vercel',
            'railway': 'npm install -g @railway/cli',
            'wrangler': 'npm install -g wrangler'
        }
        
        for tool, install_cmd in optional_tools.items():
            if not self.run_command(f"{tool} --version"):
                logger.warning(f"{tool} not found. Install with: {install_cmd}")
                
        return True
        
    def setup_environment(self) -> bool:
        """Setup environment variables."""
        
        logger.info("Setting up environment...")
        
        env_file = self.root_dir / '.env'
        env_example = self.root_dir / '.env.example'
        
        if not env_file.exists() and env_example.exists():
            logger.info("Creating .env from .env.example")
            env_file.write_text(env_example.read_text())
            logger.warning("Please update .env with your actual values")
            return False
            
        # Validate critical environment variables
        required_vars = [
            'DATABASE_URL',
            'SECRET_KEY',
            'REDDIT_CLIENT_ID',
            'REDDIT_CLIENT_SECRET'
        ]
        
        missing = []
        for var in required_vars:
            if not os.getenv(var):
                missing.append(var)
                
        if missing:
            logger.error(f"Missing environment variables: {', '.join(missing)}")
            return False
            
        return True
        
    def migrate_database(self) -> bool:
        """Migrate database to Supabase."""
        
        logger.info("Migrating database...")
        
        # Check if migration script exists
        migration_script = self.api_dir / 'scripts' / 'migrate_to_supabase.py'
        
        if not migration_script.exists():
            logger.error("Migration script not found")
            return False
            
        # Run migration in dry-run mode first
        if not self.dry_run:
            logger.info("Running database migration (dry run)...")
            if not self.run_command(
                f"python {migration_script} --dry-run",
                cwd=self.api_dir
            ):
                return False
                
            # Ask for confirmation
            response = input("Proceed with actual migration? (y/N): ")
            if response.lower() != 'y':
                logger.info("Migration cancelled")
                return False
                
        # Run actual migration
        return self.run_command(
            f"python {migration_script} --execute",
            cwd=self.api_dir
        )
        
    def deploy_backend(self) -> bool:
        """Deploy backend API."""
        
        logger.info("Deploying backend...")
        
        # Option 1: Deploy to Render
        if os.getenv('RENDER_API_KEY'):
            logger.info("Deploying to Render.com...")
            commands = [
                "git push render main",
                # Or use Render CLI if available
            ]
            
        # Option 2: Deploy to Railway
        elif os.getenv('RAILWAY_TOKEN'):
            logger.info("Deploying to Railway...")
            commands = [
                "railway login",
                "railway link",
                "railway up"
            ]
            
        # Option 3: Local deployment
        else:
            logger.info("Starting local backend...")
            commands = [
                "pip install -r requirements.txt",
                "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
            ]
            
        for cmd in commands:
            if not self.run_command(cmd, cwd=self.api_dir):
                return False
                
        return True
        
    def deploy_frontend(self) -> bool:
        """Deploy frontend application."""
        
        logger.info("Deploying frontend...")
        
        # Build frontend
        logger.info("Building frontend...")
        if not self.run_command("npm install", cwd=self.web_dir):
            return False
            
        if not self.run_command("npm run build", cwd=self.web_dir):
            return False
            
        # Deploy to Vercel
        if os.getenv('VERCEL_TOKEN'):
            logger.info("Deploying to Vercel...")
            
            commands = [
                f"vercel --token {os.getenv('VERCEL_TOKEN')} --yes",
                f"vercel --token {os.getenv('VERCEL_TOKEN')} --prod"
            ]
            
            for cmd in commands:
                if not self.run_command(cmd, cwd=self.web_dir):
                    return False
                    
        # Or start local server
        else:
            logger.info("Starting local frontend...")
            return self.run_command("npm run dev", cwd=self.web_dir)
            
        return True
        
    def setup_cloudflare_worker(self) -> bool:
        """Setup Cloudflare Worker for API proxy."""
        
        logger.info("Setting up Cloudflare Worker...")
        
        worker_dir = self.root_dir / 'workers'
        
        if not worker_dir.exists():
            logger.info("Creating worker directory...")
            worker_dir.mkdir()
            
            # Create worker script
            worker_script = worker_dir / 'api-proxy.js'
            worker_script.write_text("""
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // Route API requests to backend
    if (url.pathname.startswith('/api')) {
      const backendUrl = env.BACKEND_URL || 'https://api.waardhaven.com';
      return fetch(backendUrl + url.pathname, request);
    }
    
    // Serve frontend from Vercel
    const frontendUrl = env.FRONTEND_URL || 'https://waardhaven.vercel.app';
    return fetch(frontendUrl + url.pathname, request);
  }
};
            """)
            
            # Create wrangler.toml
            wrangler_config = worker_dir / 'wrangler.toml'
            wrangler_config.write_text("""
name = "waardhaven-api"
main = "api-proxy.js"
compatibility_date = "2024-01-01"

[env.production]
vars = { ENVIRONMENT = "production" }
            """)
            
        # Deploy worker
        if os.getenv('CLOUDFLARE_API_TOKEN'):
            return self.run_command("wrangler publish", cwd=worker_dir)
            
        logger.warning("Cloudflare API token not found, skipping worker deployment")
        return True
        
    def setup_github_actions(self) -> bool:
        """Configure GitHub Actions secrets."""
        
        logger.info("Setting up GitHub Actions...")
        
        secrets = {
            'DATABASE_URL': os.getenv('SUPABASE_DATABASE_URL'),
            'REDIS_URL': os.getenv('REDIS_URL'),
            'SECRET_KEY': os.getenv('SECRET_KEY'),
            'REDDIT_CLIENT_ID': os.getenv('REDDIT_CLIENT_ID'),
            'REDDIT_CLIENT_SECRET': os.getenv('REDDIT_CLIENT_SECRET'),
            'YOUTUBE_API_KEY': os.getenv('YOUTUBE_API_KEY'),
            'MARKETAUX_API_KEY': os.getenv('MARKETAUX_API_KEY'),
            'TWELVEDATA_API_KEY': os.getenv('TWELVEDATA_API_KEY'),
            'DISCORD_WEBHOOK': os.getenv('DISCORD_WEBHOOK')
        }
        
        for name, value in secrets.items():
            if value and not self.dry_run:
                self.run_command(f"gh secret set {name} --body '{value}'")
                
        # Enable workflows
        workflows = ['collect-signals.yml', 'ci-cd-pipeline.yml']
        
        for workflow in workflows:
            self.run_command(f"gh workflow enable {workflow}")
            
        return True
        
    def verify_deployment(self) -> bool:
        """Verify that deployment was successful."""
        
        logger.info("Verifying deployment...")
        
        checks = [
            {
                'name': 'Backend Health',
                'url': os.getenv('API_URL', 'http://localhost:8000') + '/health',
                'expected': 200
            },
            {
                'name': 'Frontend',
                'url': os.getenv('FRONTEND_URL', 'http://localhost:3000'),
                'expected': 200
            },
            {
                'name': 'Database Connection',
                'url': os.getenv('API_URL', 'http://localhost:8000') + '/api/v1/diagnostics/database',
                'expected': 200
            }
        ]
        
        import requests
        
        all_passed = True
        for check in checks:
            try:
                response = requests.get(check['url'], timeout=10)
                if response.status_code == check['expected']:
                    logger.info(f"✅ {check['name']}: OK")
                else:
                    logger.error(f"❌ {check['name']}: Failed (status: {response.status_code})")
                    all_passed = False
            except Exception as e:
                logger.error(f"❌ {check['name']}: Failed ({e})")
                all_passed = False
                
        return all_passed
        
    def deploy(self) -> bool:
        """Run full deployment process."""
        
        logger.info(f"Starting deployment to {self.target}...")
        
        steps = [
            ("Prerequisites", self.check_prerequisites),
            ("Environment Setup", self.setup_environment),
            ("Database Migration", self.migrate_database),
            ("Backend Deployment", self.deploy_backend),
            ("Frontend Deployment", self.deploy_frontend),
            ("Cloudflare Worker", self.setup_cloudflare_worker),
            ("GitHub Actions", self.setup_github_actions),
            ("Verification", self.verify_deployment)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n{'='*50}")
            logger.info(f"Step: {step_name}")
            logger.info('='*50)
            
            if not step_func():
                logger.error(f"❌ {step_name} failed")
                return False
                
            logger.info(f"✅ {step_name} completed")
            
        logger.info("\n" + "="*50)
        logger.info("🎉 Deployment completed successfully!")
        logger.info("="*50)
        
        return True


def main():
    """Main entry point."""
    
    parser = argparse.ArgumentParser(
        description='Deploy Waardhaven AutoIndex platform'
    )
    parser.add_argument(
        '--target',
        choices=['local', 'staging', 'production'],
        default='production',
        help='Deployment target'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without making actual changes'
    )
    parser.add_argument(
        '--skip-migration',
        action='store_true',
        help='Skip database migration'
    )
    parser.add_argument(
        '--backend-only',
        action='store_true',
        help='Deploy only backend'
    )
    parser.add_argument(
        '--frontend-only',
        action='store_true',
        help='Deploy only frontend'
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    from dotenv import load_dotenv
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        
    # Create deployment manager
    manager = DeploymentManager(
        target=args.target,
        dry_run=args.dry_run
    )
    
    # Override methods if specific flags are set
    if args.skip_migration:
        manager.migrate_database = lambda: True
        
    if args.backend_only:
        manager.deploy_frontend = lambda: True
        manager.setup_cloudflare_worker = lambda: True
        
    if args.frontend_only:
        manager.deploy_backend = lambda: True
        manager.migrate_database = lambda: True
        
    # Run deployment
    success = manager.deploy()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()