#!/bin/bash

echo "🚀 Starting WhatsApp Integration Platform..."

# Change to backend directory and start services
cd backend

echo "📦 Building and starting services with Docker Compose..."
docker-compose up --build -d

echo "✅ Services started!"
echo ""
echo "🌐 Access your application:"
echo "   Frontend: http://localhost:8080"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Grafana: http://localhost:3001 (admin/admin)"
echo "   Prometheus: http://localhost:9090"
echo ""
echo "📊 Health check:"
echo "   Backend: curl http://localhost:8000/health"
echo ""
echo "🛑 To stop services: docker-compose down"