# PHASE 3: CLOUD MIGRATION PLAN

**Date:** 2026-04-25  
**Status:** PLANNING  
**Estimated Duration:** 10-15 days  
**Target:** Platinum Tier Readiness

---

## EXECUTIVE SUMMARY

This document outlines the strategy for migrating the AI Employee system from single-machine deployment to cloud-native, horizontally scalable architecture. The migration will enable Platinum tier features including multi-instance deployment, distributed coordination, and enterprise-grade reliability.

**Current State:** 85/100 - Single-machine production ready  
**Target State:** 95/100 - Platinum tier ready  
**Improvement:** +10 points

---

## ARCHITECTURE OVERVIEW

### Current Architecture (Single Machine)
```
┌─────────────────────────────────────────────────────────┐
│                    Single Machine                        │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Orchestrator │  │   Watchers   │  │   Watchdog   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         │                  │                  │         │
│         └──────────────────┴──────────────────┘         │
│                          │                              │
│                  ┌───────▼────────┐                     │
│                  │  File System   │                     │
│                  │  (Vault, Logs) │                     │
│                  └────────────────┘                     │
└─────────────────────────────────────────────────────────┘
```

**Limitations:**
- Single point of failure
- Cannot scale horizontally
- File-based coordination doesn't work across machines
- No load balancing
- Limited to single machine resources

### Target Architecture (Cloud-Native)
```
┌─────────────────────────────────────────────────────────────────┐
│                        Load Balancer                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼──────┐  ┌──────▼─────┐  ┌──────▼─────┐
│ Orchestrator │  │Orchestrator│  │Orchestrator│
│  Instance 1  │  │ Instance 2 │  │ Instance 3 │
└───────┬──────┘  └──────┬─────┘  └──────┬─────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼──────┐  ┌──────▼─────┐  ┌──────▼─────┐
│    Redis     │  │   SQS/RMQ  │  │    S3/EFS  │
│ (Locking &   │  │  (Message  │  │   (Shared  │
│   Caching)   │  │   Queue)   │  │   Storage) │
└──────────────┘  └────────────┘  └────────────┘
```

**Benefits:**
- Horizontal scaling (add more instances)
- High availability (no single point of failure)
- Load balancing across instances
- Distributed coordination via Redis
- Message queue for async processing
- Shared storage for vault files

---

## MIGRATION PHASES

### Phase 3.1: Containerization (3-4 days)

**Objective:** Package all components as Docker containers

**Tasks:**
1. Create base Python Dockerfile
2. Create Dockerfile for orchestrator
3. Create Dockerfile for each watcher (gmail, whatsapp, facebook, instagram)
4. Create Dockerfile for watchdog
5. Create docker-compose.yml for local testing
6. Optimize image sizes (multi-stage builds)
7. Test local container deployment

**Deliverables:**
- `Dockerfile.base` - Base Python image with dependencies
- `Dockerfile.orchestrator` - Orchestrator container
- `Dockerfile.watcher` - Generic watcher container
- `docker-compose.yml` - Local orchestration
- `docker-compose.prod.yml` - Production configuration

**Success Criteria:**
- All services run in containers locally
- docker-compose up starts entire system
- Health checks pass in containerized environment
- Logs accessible via docker logs

---

### Phase 3.2: Distributed Coordination (3-4 days)

**Objective:** Replace file-based coordination with distributed systems

**Tasks:**

**A. Redis Integration (2 days)**
1. Add Redis client to requirements
2. Create `scripts/redis_lock.py` - Distributed locking
3. Create `scripts/redis_cache.py` - Distributed caching
4. Update orchestrator to use Redis locks instead of file locks
5. Update secrets manager to cache in Redis
6. Test multi-instance deployment with Redis

**B. Message Queue Integration (1-2 days)**
1. Choose queue system (SQS for AWS, RabbitMQ for self-hosted)
2. Create `scripts/message_queue.py` - Queue abstraction
3. Update orchestrator to publish tasks to queue
4. Update workers to consume from queue
5. Implement dead letter queue for failed tasks
6. Test async task processing

**Deliverables:**
- `scripts/redis_lock.py` - Distributed locking implementation
- `scripts/redis_cache.py` - Distributed caching
- `scripts/message_queue.py` - Queue abstraction layer
- Updated orchestrator with queue support
- Integration tests for distributed coordination

**Success Criteria:**
- Multiple orchestrator instances can run simultaneously
- No race conditions or duplicate processing
- Tasks distributed evenly across instances
- Failed tasks retry via dead letter queue

---

### Phase 3.3: Cloud Deployment (4-5 days)

**Objective:** Deploy to cloud platform (AWS/Azure/GCP)

**Tasks:**

**A. Infrastructure Setup (1-2 days)**
1. Choose cloud platform (AWS recommended)
2. Set up VPC, subnets, security groups
3. Provision Redis (ElastiCache) or equivalent
4. Provision message queue (SQS/RabbitMQ)
5. Provision shared storage (EFS/S3)
6. Set up secrets manager (AWS Secrets Manager)

**B. Kubernetes/ECS Configuration (2-3 days)**
1. Create Kubernetes manifests (or ECS task definitions)
   - Deployment for orchestrator (3 replicas)
   - Deployment for each watcher (1 replica each)
   - Deployment for watchdog (1 replica)
2. Configure health checks (liveness, readiness)
3. Configure resource limits (CPU, memory)
4. Configure auto-scaling policies
5. Set up ingress/load balancer
6. Configure persistent volumes for vault

**C. CI/CD Pipeline (1 day)**
1. Create GitHub Actions workflow (or equivalent)
2. Build and push Docker images to registry
3. Deploy to staging environment
4. Run integration tests
5. Deploy to production (manual approval)

**Deliverables:**
- `k8s/` directory with all Kubernetes manifests
- `terraform/` or `cloudformation/` for infrastructure as code
- `.github/workflows/deploy.yml` - CI/CD pipeline
- Deployment runbook
- Rollback procedures

**Success Criteria:**
- System runs in cloud environment
- Health checks pass
- Auto-scaling works (scale up/down based on load)
- Zero-downtime deployments
- Monitoring and alerting operational

---

### Phase 3.4: Secrets Migration (1-2 days)

**Objective:** Migrate from .env files to cloud secrets manager

**Tasks:**
1. Create secrets in AWS Secrets Manager (or equivalent)
2. Update secrets_manager.py to prioritize cloud backend
3. Remove .env files from production
4. Update deployment to inject secrets as environment variables
5. Test end-to-end with cloud secrets
6. Document secret rotation procedures

**Deliverables:**
- All secrets in cloud secrets manager
- Updated secrets_manager.py with cloud priority
- Secret rotation automation scripts
- Documentation for adding new secrets

**Success Criteria:**
- No .env files in production
- All services read secrets from cloud
- Secret rotation works without downtime
- Audit trail for secret access

---

## COMPONENT MIGRATION DETAILS

### Orchestrator
**Current:** Single process, file-based locking  
**Target:** Multiple instances, Redis locking, queue-based task distribution

**Changes:**
- Replace `file_locking.py` with `redis_lock.py`
- Add message queue consumer
- Add health check endpoint
- Add graceful shutdown handler
- Add distributed tracing (correlation IDs)

### Watchers
**Current:** Single instance per watcher type  
**Target:** Stateless, can run multiple instances

**Changes:**
- Add Redis-based duplicate detection
- Add message queue publisher
- Add health check endpoint
- Make heartbeat Redis-based (not file-based)
- Add graceful shutdown handler

### Watchdog
**Current:** Monitors file-based heartbeats  
**Target:** Monitors Redis-based heartbeats, sends alerts to multiple channels

**Changes:**
- Check Redis for heartbeats instead of files
- Add Prometheus metrics export
- Add PagerDuty integration
- Add auto-restart capability (via Kubernetes)

### Vault Storage
**Current:** Local filesystem  
**Target:** Shared storage (EFS/S3)

**Changes:**
- Mount EFS volume to all pods
- Or use S3 with local caching
- Add file sync mechanism
- Add backup/restore procedures

---

## TECHNOLOGY STACK

### Container Orchestration
**Option A: Kubernetes (Recommended)**
- Pros: Industry standard, rich ecosystem, multi-cloud
- Cons: Complex, steep learning curve
- Best for: Long-term scalability, multi-cloud strategy

**Option B: AWS ECS**
- Pros: Simpler, AWS-native, good integration
- Cons: AWS lock-in, less flexible
- Best for: AWS-only deployment, faster time to market

**Recommendation:** Start with ECS for faster deployment, migrate to Kubernetes later if needed

### Distributed Coordination
**Redis (Recommended)**
- Distributed locking (Redlock algorithm)
- Distributed caching
- Pub/sub for real-time updates
- Session storage

### Message Queue
**Option A: AWS SQS (Recommended for AWS)**
- Pros: Fully managed, scalable, reliable
- Cons: AWS lock-in, eventual consistency
- Best for: AWS deployment

**Option B: RabbitMQ**
- Pros: Feature-rich, self-hosted, strong consistency
- Cons: Requires management, more complex
- Best for: Self-hosted or multi-cloud

**Recommendation:** SQS for AWS, RabbitMQ for self-hosted

### Shared Storage
**Option A: AWS EFS (Recommended)**
- Pros: NFS-compatible, automatic scaling, multi-AZ
- Cons: More expensive, performance limits
- Best for: File-based vault storage

**Option B: S3 + Local Cache**
- Pros: Cheaper, unlimited scale, durable
- Cons: Not POSIX, requires caching layer
- Best for: Large-scale, cost-sensitive

**Recommendation:** EFS for simplicity, S3 for scale

---

## DEPLOYMENT STRATEGY

### Blue-Green Deployment
1. Deploy new version (green) alongside old version (blue)
2. Run health checks on green
3. Gradually shift traffic from blue to green (10% → 50% → 100%)
4. Monitor metrics and error rates
5. Rollback to blue if issues detected
6. Decommission blue after 24 hours

### Canary Deployment
1. Deploy new version to 5% of instances
2. Monitor for 1 hour
3. If healthy, increase to 25%
4. Monitor for 1 hour
5. If healthy, increase to 100%
6. Rollback at any stage if issues detected

**Recommendation:** Blue-green for major changes, canary for minor updates

---

## MONITORING & OBSERVABILITY

### Metrics (Prometheus)
- Request rate, latency, error rate (RED metrics)
- CPU, memory, disk usage
- Queue depth, processing time
- Cache hit rate
- Active connections

### Logging (CloudWatch/ELK)
- Structured JSON logs
- Correlation IDs for request tracing
- Log aggregation across instances
- Log retention policies (30 days)

### Tracing (Jaeger/X-Ray)
- Distributed tracing across services
- Request flow visualization
- Performance bottleneck identification

### Alerting (PagerDuty)
- Critical: Service down, high error rate
- Warning: High latency, resource exhaustion
- Info: Deployment events, scaling events

---

## COST ESTIMATION

### AWS (us-east-1, monthly)
- **ECS Fargate:** 3 orchestrator instances (0.5 vCPU, 1GB RAM) = $30
- **ECS Fargate:** 4 watcher instances (0.25 vCPU, 0.5GB RAM) = $20
- **ElastiCache Redis:** cache.t3.micro = $15
- **SQS:** 1M requests = $0.40
- **EFS:** 10GB storage = $3
- **Secrets Manager:** 10 secrets = $4
- **CloudWatch Logs:** 10GB ingestion = $5
- **Load Balancer:** ALB = $20
- **Data Transfer:** 100GB = $9

**Total:** ~$106/month

**Scaling:** Add $10/month per additional orchestrator instance

---

## RISKS & MITIGATION

### Risk 1: Data Loss During Migration
**Mitigation:**
- Full backup before migration
- Test restore procedures
- Parallel run (old + new) for 1 week
- Gradual cutover with rollback plan

### Risk 2: Performance Degradation
**Mitigation:**
- Load testing before production
- Gradual traffic shift (canary deployment)
- Performance monitoring and alerting
- Auto-scaling to handle load spikes

### Risk 3: Increased Complexity
**Mitigation:**
- Comprehensive documentation
- Runbooks for common operations
- Training for team members
- Gradual rollout (one component at a time)

### Risk 4: Cost Overruns
**Mitigation:**
- Cost monitoring and alerts
- Right-sizing instances (start small)
- Reserved instances for predictable workloads
- Auto-scaling to avoid over-provisioning

---

## SUCCESS METRICS

### Technical Metrics
- **Uptime:** 99.9% (8.76 hours downtime/year)
- **Latency:** p95 < 500ms, p99 < 1s
- **Error Rate:** < 0.1%
- **Deployment Frequency:** Daily
- **Mean Time to Recovery:** < 15 minutes

### Business Metrics
- **Scalability:** Handle 10x current load
- **Availability:** 24/7 operation
- **Cost Efficiency:** < $200/month for baseline
- **Time to Market:** New features deployed in < 1 day

---

## TIMELINE

### Week 1: Containerization
- Days 1-2: Create Dockerfiles
- Days 3-4: Test local deployment
- Day 5: Optimize images

### Week 2: Distributed Coordination
- Days 1-2: Redis integration
- Days 3-4: Message queue integration
- Day 5: Integration testing

### Week 3: Cloud Deployment
- Days 1-2: Infrastructure setup
- Days 3-4: Kubernetes/ECS configuration
- Day 5: Staging deployment

### Week 4: Production & Secrets
- Days 1-2: Production deployment
- Days 3-4: Secrets migration
- Day 5: Final testing & documentation

**Total:** 4 weeks (20 working days)

---

## ROLLBACK PLAN

### If Migration Fails
1. Stop new deployment
2. Redirect traffic to old system
3. Investigate root cause
4. Fix issues in staging
5. Retry migration

### Rollback Triggers
- Error rate > 1%
- Latency p99 > 5s
- Uptime < 99%
- Data inconsistencies detected
- Critical functionality broken

### Rollback Procedure
1. Scale down new deployment to 0
2. Scale up old deployment
3. Update DNS/load balancer
4. Verify old system operational
5. Post-mortem and fix

---

## NEXT STEPS

### Immediate (This Week)
1. ✅ Create Dockerfiles for all components
2. ✅ Test local docker-compose deployment
3. ⬜ Choose cloud platform (AWS recommended)
4. ⬜ Set up AWS account and IAM roles

### Short-term (Next 2 Weeks)
1. ⬜ Implement Redis locking
2. ⬜ Implement message queue
3. ⬜ Test multi-instance deployment locally
4. ⬜ Create Kubernetes manifests

### Long-term (Next Month)
1. ⬜ Deploy to staging environment
2. ⬜ Load testing and optimization
3. ⬜ Production deployment
4. ⬜ Secrets migration
5. ⬜ Documentation and training

---

**Plan Created:** 2026-04-25  
**Plan Owner:** AI Systems Engineer  
**Next Review:** After Phase 3.1 completion  
**Related:** PHASES-1-2-COMPLETE-SUMMARY.md, AUDIT-1-COMPLETION-STATUS.md
