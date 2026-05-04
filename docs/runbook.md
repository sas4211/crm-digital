# Incident Response Runbook — Customer Success FTE

## How to Use This Runbook

| Priority | Response Time | Notification |
|---|---|---|
| **P1** — Service down | 15 min | PagerDuty |
| **P2** — Channel degraded | 1 hour | Slack #support-alerts |
| **P3** — Elevated errors | 4 hours | Slack #support-alerts |
| **P4** — Minor issue / doc | Next business day | Email |

---

## 1. Service Unhealthy (P1)

**Symptom:** `/health` returns non-200 or API pods crashing.

**Checks:**
```bash
kubectl -n customer-success-fte get pods
kubectl -n customer-success-fte describe pod <pod>
kubectl -n customer-success-fte logs <pod> -f
```

**Actions:**
1. Check pod restarts — `kubectl get pods | awk '/Restart/'`
2. Verify DB connectivity — `kubectl exec -it <postgres-pod> -- pg_isready`
3. Verify Kafka — `kubectl -n kafka exec kafka-0 -- kafka-topics.sh --bootstrap-server localhost:9092 --list`
4. Roll back — `kubectl rollout undo deployment/fte-api`
5. Scale down — `kubectl scale --replicas=3 deployment/fte-api`

---

## 2. Channel Degraded (P2)

### 2.1 Gmail Down

**Symptom:** Email webhook errors, high DLQ rate.

**Checks:**
```bash
kubectl logs -l component=fte-api -f | grep "gmail"
```

**Actions:**
1. Check Gmail API quota — Google Cloud Console → APIs & Services → Quotas
2. Verify credentials — `kubectl get secret fte-secrets -o jsonpath='{.data.GMAIL_CREDENTIALS}' | base64 -d`
3. Refresh token — re-auth via `gcloud auth login`

### 2.2 WhatsApp Down

**Symptom:** Twilio webhook failures or message delivery failures.

**Checks:**
```bash
kubectl logs -l component=fte-api -f | grep "whatsapp"
```

**Actions:**
1. Check Twilio dashboard — https://console.twilio.com
2. Verify webhook URL — Twilio Console → WhatsApp → Sandbox → Webhook URL
3. Check account balance — low balance will block sends

---

## 3. Elevated LLM Error Rate (P2/P3)

**Symptom:** Agent returns fallback messages, low success rate on `/metrics`.

**Checks:**
```bash
curl http://localhost:8000/metrics
# Check: success_rate < 0.9 or error_count > 0
```

**Actions:**
1. Check Gemini quota — Google AI Studio → Usage
2. Verify `GEMINI_API_KEY` is valid and not expired
3. If rate-limited, reduce request rate at the worker (`--replicas` scale up)
4. Monitor `/metrics/channels` for per-channel degradation

---

## 4. Database Overload (P2)

**Symptom:** Slow conversations, high latency on `/conversations/{id}`.

**Checks:**
```bash
kubectl exec -it <postgres-pod> -- pg_stat_activity
kubectl exec -it <postgres-pod> -- "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"
```

**Actions:**
1. Check connection pool — asyncpg pool size should not exceed `max_connections`
2. Kill long-running queries — `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND query_start < NOW() - INTERVAL '1 hour';`
3. Check indexes — `SELECT * FROM pg_stat_user_indexes WHERE idx_scan = 0;`
4. If disk full — extend PVC or archive old data

---

## 5. Kafka Consumer Lag (P2)

**Symptom:** Messages not being processed, growing DLQ.

**Checks:**
```bash
kubectl -n kafka exec kafka-0 -- kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group fte-message-processor
```

**Actions:**
1. Check worker pods — `kubectl get pods -l component=message-processor`
2. Scale workers — `kubectl scale --replicas=6 deployment/fte-message-processor`
3. Review DLQ — `kubectl -n kafka exec kafka-0 -- kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic fte.dlq --from-beginning`
4. Fix root cause, then reset consumer offsets if needed

---

## Quick Diagnostic Commands

```bash
# All pods + status
kubectl -n customer-success-fte get pods

# Recent logs (last 50 lines)
kubectl -n customer-success-fte logs --tail=50 -l app=customer-success-fte

# Service DNS resolution
kubectl -n customer-success-fte exec <pod> -- nslookup customer-success-fte

# Check ingress
kubectl -n customer-success-fte get ingress
```
