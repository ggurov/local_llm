#!/bin/bash
# Setup script for Local LLM Stack

set -e

echo "🚀 Setting up Local LLM Stack..."
echo "================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root"
   exit 1
fi

# Check for required tools
echo "🔍 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check NVIDIA Docker runtime
if ! docker info | grep -q nvidia; then
    echo "⚠️  NVIDIA Docker runtime not detected. GPU acceleration may not work."
    echo "   Install nvidia-docker2 for GPU support."
fi

# Check NVIDIA drivers
if ! command -v nvidia-smi &> /dev/null; then
    echo "⚠️  nvidia-smi not found. NVIDIA drivers may not be installed."
else
    echo "✅ NVIDIA drivers detected:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits
fi

# Check available disk space
AVAILABLE_SPACE=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -lt 50 ]; then
    echo "⚠️  Low disk space: ${AVAILABLE_SPACE}GB available. At least 50GB recommended."
fi

echo "✅ Prerequisites check completed"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/qdrant data/langfuse data/hf_cache
chmod 755 data/qdrant data/langfuse data/hf_cache

# Set up environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env 2>/dev/null || echo "⚠️  .env.example not found, using default .env"
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x scripts/*.py scripts/*.sh

# Pull Docker images
echo "🐳 Pulling Docker images..."
docker compose pull

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Review and update .env file if needed"
echo "2. Run 'make up' to start all services"
echo "3. Run 'make health' to check service status"
echo "4. Run 'make smoke' to run smoke tests"
echo ""
echo "For more commands, run 'make help'"

