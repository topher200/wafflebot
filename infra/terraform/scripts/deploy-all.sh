#!/bin/bash

# Deploy All Infrastructure Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Deploying All WaffleBot Infrastructure..."
echo ""

# Deploy podcast staging
echo "1️⃣  Deploying Podcast Staging..."
"$SCRIPT_DIR/deploy-podcast.sh" staging

echo ""
echo "2️⃣  Deploying Podcast Production..."
"$SCRIPT_DIR/deploy-podcast.sh" prod

echo ""
echo "3️⃣  Deploying Test Files..."
"$SCRIPT_DIR/deploy-test-files.sh"

echo ""
echo "✅ All infrastructure deployed successfully!"
echo ""
echo "📋 Summary:"
echo "   🎙️  Podcast Staging: deployed"
echo "   🎙️  Podcast Production: deployed"
echo "   🧪 Test Files: deployed"
