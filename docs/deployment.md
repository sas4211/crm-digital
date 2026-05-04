# Deployment & Operations Guide

## 1. Local Development (docker-compose)

```bash
cd production/
docker compose up -d
```

Starts 3 services:
- **postgres** (init with schema) — port 5432
- **kafka** (KRaft, no Zookeeper) — port 9092
- **api** (FastAPI app) — port 8000

Verify: `curl http://localhost:8000/health`

## 2. Kubernetes Deployment (Production)

```bash
# Set env vars before creating secrets
export GEMINI_API_KEY="..."
export POSTGRES_PASSWORD="..."
export TWILIO_ACCOUNT_SID="..."
export TWILIO_AUTH_TOKEN="..."
export TWILIO_WHATSAPP_NUMBER="whatsapp:+14155238886"

# Apply in order
kubectl apply -f production/k8s/namespace.yaml
kubectl apply -f production/k8s/configmap.yaml
kubectl apply -f production/k8s/secrets.yaml
kubectl apply -f production/k8s/deployment-api.yaml
kubectl apply -f production/k8s/deployment-worker.yaml
kubectl apply -f production/k8s/service.yaml
kubectl apply -f production/k8s/ingress.yaml
kubectl apply -f production/k8s/hpa.yaml
```

## 3. External Dependencies

| Service | Purpose | Required Vars |
|---|---|---|
| Google Gemini | LLM inference | `GEMINI_API_KEY` |
| Twilio | WhatsApp messages | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` |
| Postgres | CRM data store | `DATABASE_URL` |
| Kafka | Event streaming | `KAFKA_BOOTSTRAP_SERVERS` |

## 4. Architecture

```
Channel → Kafka → UnifiedMessageProcessor → Gemini Agent → Kafka Response Consumer → Channel
```
