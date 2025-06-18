#!/bin/bash
# GitHub Backup Setup Script for Windows (PowerShell)
# Run this script after installing Git

# Colors for output
$GREEN = "`e[32m"
$BLUE = "`e[34m"
$YELLOW = "`e[33m"
$RED = "`e[31m"
$NC = "`e[0m" # No Color

Write-Host "${BLUE}🚀 Setting up GitHub backup for LLM Backend${NC}"
Write-Host ""

# Check if Git is installed
try {
    $gitVersion = git --version
    Write-Host "${GREEN}✅ Git found: $gitVersion${NC}"
} catch {
    Write-Host "${RED}❌ Git not found. Please install Git first:${NC}"
    Write-Host "   Download from: https://git-scm.com/download/win"
    Write-Host "   Or run: winget install --id Git.Git -e --source winget"
    exit 1
}

# Initialize git repository if not already initialized
if (-not (Test-Path ".git")) {
    Write-Host "${YELLOW}📁 Initializing Git repository...${NC}"
    git init
    Write-Host "${GREEN}✅ Git repository initialized${NC}"
} else {
    Write-Host "${GREEN}✅ Git repository already exists${NC}"
}

# Configure Git (update with your details)
Write-Host "${YELLOW}⚙️ Git configuration...${NC}"
$userName = Read-Host "Enter your GitHub username"
$userEmail = Read-Host "Enter your GitHub email"

git config user.name "$userName"
git config user.email "$userEmail"
Write-Host "${GREEN}✅ Git configured for $userName <$userEmail>${NC}"

# Create initial commit
Write-Host "${YELLOW}📝 Creating initial commit...${NC}"
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

Write-Host "${GREEN}✅ Initial commit created${NC}"

# Instructions for GitHub
Write-Host ""
Write-Host "${BLUE}🌐 Next steps for GitHub upload:${NC}"
Write-Host ""
Write-Host "1. Create a new repository on GitHub:"
Write-Host "   - Go to https://github.com/new"
Write-Host "   - Repository name: ${YELLOW}advanced-llm-backend${NC}"
Write-Host "   - Description: ${YELLOW}Enterprise FastAPI backend with tool-augmented AI and adaptive learning${NC}"
Write-Host "   - Keep it ${YELLOW}Public${NC} (or Private if preferred)"
Write-Host "   - ${RED}DO NOT${NC} initialize with README, .gitignore, or license"
Write-Host ""
Write-Host "2. After creating the repository, run these commands:"
Write-Host "   ${YELLOW}git branch -M main${NC}"
Write-Host "   ${YELLOW}git remote add origin https://github.com/$userName/advanced-llm-backend.git${NC}"
Write-Host "   ${YELLOW}git push -u origin main${NC}"
Write-Host ""
Write-Host "3. Your repository will be available at:"
Write-Host "   ${BLUE}https://github.com/$userName/advanced-llm-backend${NC}"
Write-Host ""
Write-Host "${GREEN}🎉 Backup setup complete!${NC}"
Write-Host ""
Write-Host "${YELLOW}⚠️  Important Security Notes:${NC}"
Write-Host "- Your .env files with API keys are NOT included (protected by .gitignore)"
Write-Host "- Large model files are excluded to stay within GitHub limits"
Write-Host "- Use .env.example as a template for configuration"
Write-Host "- Consider using GitHub Secrets for sensitive data in CI/CD"
