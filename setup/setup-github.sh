#!/bin/bash
# GitHub Backup Setup Script for LLM Backend
# Run this script after installing Git

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up GitHub backup for LLM Backend${NC}"
echo ""

# Check if Git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git not found. Please install Git first:${NC}"
    echo "   Download from: https://git-scm.com/download/win"
    echo "   Or run: winget install --id Git.Git -e --source winget"
    exit 1
fi

echo -e "${GREEN}✅ Git found: $(git --version)${NC}"

# Initialize git repository if not already initialized
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}📁 Initializing Git repository...${NC}"
    git init
    echo -e "${GREEN}✅ Git repository initialized${NC}"
else
    echo -e "${GREEN}✅ Git repository already exists${NC}"
fi

# Configure Git
echo -e "${YELLOW}⚙️ Git configuration...${NC}"
read -p "Enter your GitHub username: " username
read -p "Enter your GitHub email: " email

git config user.name "$username"
git config user.email "$email"
echo -e "${GREEN}✅ Git configured for $username <$email>${NC}"

# Create initial commit
echo -e "${YELLOW}📝 Creating initial commit...${NC}"
git add .
git commit -m "Initial commit: Advanced LLM Backend with Tool Integration

Features:
- 🤖 Local LLM with llama3.2:3b model
- 🛠️ 8 AI tools (Python, web search, weather, math, etc.)
- 🧠 Adaptive learning system with feedback loops
- 📄 Enhanced document processing (5 strategies)
- 🏥 24/7 health monitoring and auto-recovery
- 🔒 Enterprise security and error handling
- 🐳 Docker deployment with persistent storage
- 📚 Complete documentation and API reference

System Status: Production Ready ✅"

echo -e "${GREEN}✅ Initial commit created${NC}"

# Instructions for GitHub
echo ""
echo -e "${BLUE}🌐 Next steps for GitHub upload:${NC}"
echo ""
echo "1. Create a new repository on GitHub:"
echo "   - Go to https://github.com/new"
echo -e "   - Repository name: ${YELLOW}advanced-llm-backend${NC}"
echo -e "   - Description: ${YELLOW}Enterprise FastAPI backend with tool-augmented AI and adaptive learning${NC}"
echo -e "   - Keep it ${YELLOW}Public${NC} (or Private if preferred)"
echo -e "   - ${RED}DO NOT${NC} initialize with README, .gitignore, or license"
echo ""
echo "2. After creating the repository, run these commands:"
echo -e "   ${YELLOW}git branch -M main${NC}"
echo -e "   ${YELLOW}git remote add origin https://github.com/$username/advanced-llm-backend.git${NC}"
echo -e "   ${YELLOW}git push -u origin main${NC}"
echo ""
echo "3. Your repository will be available at:"
echo -e "   ${BLUE}https://github.com/$username/advanced-llm-backend${NC}"
echo ""
echo -e "${GREEN}🎉 Backup setup complete!${NC}"
echo ""
echo -e "${YELLOW}⚠️  Important Security Notes:${NC}"
echo "- Your .env files with API keys are NOT included (protected by .gitignore)"
echo "- Large model files are excluded to stay within GitHub limits"
echo "- Use .env.example as a template for configuration"
echo "- Consider using GitHub Secrets for sensitive data in CI/CD"
