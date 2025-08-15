#!/bin/bash

# LASO Health Frontend Setup Script
echo "🚀 Setting up LASO Health Frontend..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version 18 or higher is required. Current version: $(node -v)"
    exit 1
fi

echo "✅ Node.js version: $(node -v)"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm."
    exit 1
fi

echo "✅ npm version: $(npm -v)"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "🔧 Creating .env file..."
    cat > .env << EOF
# LASO Health Frontend Environment Variables
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=LASO Health
VITE_APP_VERSION=1.0.0
EOF
    echo "✅ .env file created"
else
    echo "✅ .env file already exists"
fi

# Check if TypeScript is working
echo "🔍 Checking TypeScript configuration..."
npx tsc --noEmit

if [ $? -eq 0 ]; then
    echo "✅ TypeScript configuration is valid"
else
    echo "⚠️  TypeScript configuration has issues, but setup can continue"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p src/components/ui
mkdir -p src/modules/auth
mkdir -p src/modules/patient
mkdir -p src/modules/doctor
mkdir -p src/modules/layout
mkdir -p src/hooks
mkdir -p src/lib
mkdir -p src/styles

echo "✅ Directories created"

# Display next steps
echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Start the development server:"
echo "   npm run dev"
echo ""
echo "2. Open your browser and navigate to:"
echo "   http://localhost:5173"
echo ""
echo "3. To build for production:"
echo "   npm run build"
echo ""
echo "4. To preview production build:"
echo "   npm run preview"
echo ""
echo "📚 For more information, check the README.md file"
echo ""
echo "Happy coding! 🚀"
