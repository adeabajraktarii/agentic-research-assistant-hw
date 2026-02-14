# Postmortem: Vendor Credential Delay

**Incident Window:** Week 11–12  
**Severity:** Medium  
**Owner:** Engineering + Product

## Summary
A delay in receiving credentials from an external vendor blocked full integration testing for the payment service.

## Impact
- Partial test coverage
- Increased risk for Week 14 client demo
- Additional coordination overhead

## Root Cause
- Vendor onboarding process not clearly defined
- No escalation path documented

## What Went Well
- Early detection during weekly sync
- Partial mocks allowed limited progress

## What Went Wrong
- No SLA defined with vendor
- Dependency risk underestimated

## Action Items
- Define vendor SLAs
- Add escalation contacts
- Document integration prerequisites
