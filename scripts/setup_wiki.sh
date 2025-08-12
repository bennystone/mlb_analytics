#!/bin/bash

# MLB Analytics Platform - GitHub Wiki Setup Script
# This script helps set up the GitHub Wiki with our documentation

set -e

echo "🏟️  MLB Analytics Platform - GitHub Wiki Setup"
echo "================================================"

# Check if we're in the right directory
if [ ! -f "README.md" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Create wiki directory if it doesn't exist
WIKI_DIR="wiki"
if [ ! -d "$WIKI_DIR" ]; then
    echo "📁 Creating wiki directory..."
    mkdir -p "$WIKI_DIR"
fi

# Copy documentation files to wiki directory
echo "📋 Copying documentation files..."

# Copy wiki files from docs/wiki to wiki directory
if [ -d "docs/wiki" ]; then
    cp -r docs/wiki/* "$WIKI_DIR/"
    echo "✅ Copied wiki files from docs/wiki/"
else
    echo "⚠️  Warning: docs/wiki directory not found"
fi

# Create additional wiki files
echo "📝 Creating additional wiki files..."

# Create Home.md if it doesn't exist
if [ ! -f "$WIKI_DIR/Home.md" ]; then
    cat > "$WIKI_DIR/Home.md" << 'EOF'
# 🏟️ MLB Analytics Platform

A production-grade MLB data analytics platform demonstrating enterprise-level software engineering skills.

## Quick Links
- [Getting Started](Getting-Started)
- [API Documentation](API-Documentation)
- [Architecture & Design](Architecture-Design)

## Live Demo
- API: https://mlb-analytics-api-xxxxx-uc.a.run.app
- Dashboard: https://mlb-analytics-dashboard-xxxxx-uc.a.run.app

## Features
- Real-time MLB standings and playoff probabilities
- Statistical leaderboards
- Season projections
- Production-grade API with comprehensive testing
EOF
    echo "✅ Created Home.md"
fi

# Create _Sidebar.md for navigation
cat > "$WIKI_DIR/_Sidebar.md" << 'EOF'
# MLB Analytics Platform

## 📚 Documentation
- [Home](Home)
- [Getting Started](Getting-Started)
- [API Documentation](API-Documentation)
- [Architecture & Design](Architecture-Design)
- [Analytics & Models](Analytics-Models)
- [Development Guide](Development-Guide)
- [Integration Guide](Integration-Guide)
- [Troubleshooting](Troubleshooting)

## 🔗 Quick Links
- [GitHub Repository](https://github.com/yourusername/mlb_analytics)
- [Live API](https://mlb-analytics-api-xxxxx-uc.a.run.app)
- [Live Dashboard](https://mlb-analytics-dashboard-xxxxx-uc.a.run.app)
EOF
echo "✅ Created _Sidebar.md"

# Create README for the wiki
cat > "$WIKI_DIR/README.md" << 'EOF'
# MLB Analytics Platform Wiki

This directory contains the GitHub Wiki documentation for the MLB Analytics Platform.

## Setup Instructions

1. **Enable GitHub Wiki**: Go to your repository settings and enable the Wiki feature
2. **Clone the wiki**: `git clone https://github.com/yourusername/mlb_analytics.wiki.git`
3. **Copy files**: Copy all files from this `wiki/` directory to the cloned wiki repository
4. **Commit and push**: 
   ```bash
   git add .
   git commit -m "Add comprehensive documentation"
   git push origin main
   ```

## File Structure

- `Home.md` - Main wiki homepage
- `_Sidebar.md` - Navigation sidebar
- `Getting-Started.md` - Setup and development guide
- `API-Documentation.md` - Complete API reference
- `Architecture-Design.md` - System design documentation
- `Analytics-Models.md` - Statistical methodologies
- `Development-Guide.md` - Contributing guidelines
- `Integration-Guide.md` - Frontend integration
- `Troubleshooting.md` - Common issues and solutions

## Customization

Update the following placeholders in the documentation:
- `yourusername` - Your GitHub username
- `mlb-analytics-api-xxxxx-uc.a.run.app` - Your actual API URL
- `mlb-analytics-dashboard-xxxxx-uc.a.run.app` - Your actual dashboard URL
EOF
echo "✅ Created README.md"

echo ""
echo "🎉 Wiki setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Enable GitHub Wiki in your repository settings"
echo "2. Clone the wiki: git clone https://github.com/yourusername/mlb_analytics.wiki.git"
echo "3. Copy files from ./wiki/ to the cloned wiki repository"
echo "4. Update URLs and usernames in the documentation"
echo "5. Commit and push the wiki changes"
echo ""
echo "📁 Wiki files created in: ./wiki/"
echo "📖 Documentation files:"
ls -la "$WIKI_DIR/"

echo ""
echo "🔧 To enable GitHub Wiki:"
echo "1. Go to your GitHub repository"
echo "2. Click 'Settings' tab"
echo "3. Scroll down to 'Features' section"
echo "4. Check 'Wikis' to enable"
echo "5. Click 'Save'"
