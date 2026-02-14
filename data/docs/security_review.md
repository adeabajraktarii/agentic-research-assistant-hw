# Security Review – Week 12

**Scope:** Payment endpoints + public API  
**Status:** In Progress  
**Reviewer:** Security Team (Lead: Priya N.)

## Findings
### S-001: Rate Limiting Missing on Public Endpoints
- **Risk:** Abuse, brute force attempts, DoS amplification
- **Recommendation:** Add rate limiting per IP + per user token
- **Owner:** Security Team + Platform Engineering
- **Target:** Week 15

### S-002: Input Validation Inconsistent
- **Risk:** Injection vectors, malformed payload crashes
- **Recommendation:** Central validation layer + strict schema checks
- **Owner:** Platform Engineering
- **Target:** Week 15

### S-003: Secrets Handling in Local Dev
- **Risk:** Key leakage via logs or repo
- **Recommendation:** Ensure `.env` is gitignored; rotate leaked keys; document local setup
- **Owner:** DevOps
- **Target:** Week 13

## Sign-off Criteria
- Rate limiting deployed
- Input validation enforced
- Payment endpoints reviewed and test evidence attached
- Pen-test scheduled before production release
