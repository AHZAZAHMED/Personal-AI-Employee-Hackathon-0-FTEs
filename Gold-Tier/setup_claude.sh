#!/bin/bash
# Quick Setup Script for Claude API Migration
# Run this after getting your Anthropic API key

echo "=========================================="
echo "Claude API Migration - Quick Setup"
echo "=========================================="
echo ""

# Step 1: Check Python
echo "[1/5] Checking Python installation..."
if ! command -v python &> /dev/null; then
    echo "ERROR: Python not found. Please install Python 3.8+"
    exit 1
fi
echo "✓ Python found: $(python --version)"
echo ""

# Step 2: Install Anthropic SDK
echo "[2/5] Installing Anthropic SDK..."
pip install anthropic python-dotenv
echo ""

# Step 3: Check .env file
echo "[3/5] Checking .env configuration..."
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found"
    exit 1
fi

if grep -q "ANTHROPIC_API_KEY=your_anthropic_api_key_here" .env; then
    echo "⚠ WARNING: ANTHROPIC_API_KEY not set in .env"
    echo ""
    echo "Please update .env with your API key:"
    echo "  1. Get key from: https://console.anthropic.com/"
    echo "  2. Edit .env file"
    echo "  3. Replace 'your_anthropic_api_key_here' with your actual key"
    echo ""
    read -p "Press Enter after updating .env, or Ctrl+C to exit..."
fi

if grep -q "ANTHROPIC_API_KEY=sk-ant-" .env; then
    echo "✓ ANTHROPIC_API_KEY found in .env"
else
    echo "⚠ WARNING: API key may not be set correctly"
fi
echo ""

# Step 4: Test Claude API
echo "[4/5] Testing Claude API connection..."
python -c "
import sys
sys.path.insert(0, 'scripts')
from claude_ai_integration import call_claude
response = call_claude('Say Hello!')
if response:
    print('✓ Claude API working!')
    print(f'  Response: {response[:50]}...')
else:
    print('✗ Claude API test failed')
    sys.exit(1)
" 2>&1

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Claude API test failed"
    echo "Please check:"
    echo "  1. ANTHROPIC_API_KEY is correct in .env"
    echo "  2. You have API credits"
    echo "  3. Internet connection is working"
    exit 1
fi
echo ""

# Step 5: Run full test suite
echo "[5/5] Running full test suite..."
python test_claude_integration.py
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Test with: python scripts/orchestrator.py --vault AI_Employee_Vault --once"
echo "  2. Monitor usage at: https://console.anthropic.com/"
echo "  3. Check CLAUDE-MIGRATION.md for detailed docs"
echo ""
