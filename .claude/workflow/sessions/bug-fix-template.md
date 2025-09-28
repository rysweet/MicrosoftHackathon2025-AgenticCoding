# Bug Fix Session Template

## Session Efficiency Target: 4-6 exchanges

This template optimizes bug fix sessions through comprehensive upfront diagnosis and structured resolution approach.

## Pre-Session Checklist

Before starting investigation:

- [ ] Complete problem description captured
- [ ] Reproduction steps documented
- [ ] Environmental context gathered
- [ ] Impact assessment completed
- [ ] Initial hypothesis formed

## Exchange Flow Template

### Exchange 1: Complete Problem Context Gathering

**Goal**: Capture all diagnostic information in single exchange

```
To efficiently diagnose and fix this issue, I need complete context in one go:

**Problem Details:**
1. What are the exact steps to reproduce this issue?
2. What is the expected behavior vs actual behavior? (with specific examples)
3. What error messages, logs, or stack traces are available?
4. When did this issue first start happening?
5. What changes were made recently that might be related?

**Environment Context:**
6. Which environment(s) are affected? (dev/staging/prod)
7. Is this reproducible locally on your machine?
8. What browser/OS/device details are relevant?
9. Are there any workarounds currently being used?
10. What's the frequency of occurrence? (always/sometimes/rarely)

**Impact Assessment:**
11. How many users or systems are affected?
12. Is this blocking other work or critical functionality?
13. Is there risk of data loss or corruption?
14. What's the business impact? (revenue/reputation/operations)

**Technical Context:**
15. Which specific components, services, or modules are involved?
16. Are there relevant application logs, server logs, or monitoring data?
17. What debugging steps have already been attempted?
18. Are there similar issues elsewhere in the codebase?
19. What was the last known working state?

**Resources Available:**
20. Do you have access to logs/monitoring for the timeframe?
21. Can you provide screenshots, recordings, or data samples?
22. Are there test cases that should be passing but aren't?
```

### Exchange 2: Diagnostic Plan and Reproduction

**Goal**: Confirm problem understanding and execute diagnostic plan

```
## Bug Analysis: [Issue Summary]

### Problem Understanding
**Issue**: [Clear description based on provided context]
**Impact**: [Severity and scope from context]
**Environment**: [Affected systems from context]

### Reproduction Plan
**Steps to reproduce** (based on your provided steps):
1. [Step 1 - verified/clarified]
2. [Step 2 - verified/clarified]
3. [Expected]: [Expected behavior]
4. [Actual]: [Actual behavior observed]

### Diagnostic Strategy
**Investigation Areas**:
- [Area 1]: [Why this might be the cause]
- [Area 2]: [Why this might be the cause]
- [Area 3]: [Why this might be the cause]

**Data Collection**:
- [Log analysis]: [What to look for]
- [Code review]: [Specific modules to examine]
- [Testing]: [Specific scenarios to validate]

**Hypothesis Formation**:
Primary hypothesis: [Most likely cause based on context]
Secondary hypotheses: [Alternative explanations]

Proceeding with reproduction and diagnostic analysis...
```

### Exchange 3: Root Cause Analysis and Solution Design

**Goal**: Present findings and comprehensive solution plan

```
## Root Cause Analysis Complete

### Findings
**Root Cause Identified**: [Specific technical cause]
**Why it happens**: [Mechanism of failure]
**Why it wasn't caught**: [Gap in testing/monitoring]

### Evidence
- [Log evidence]: [Specific findings]
- [Code analysis]: [Problematic code sections]
- [Data evidence]: [Database/state issues]
- [Timeline correlation]: [When/how it started]

### Solution Design
**Primary Fix**:
- [What needs to be changed]
- [Why this approach solves the root cause]
- [Risk assessment of the fix]

**Secondary Measures**:
- [Monitoring improvements]
- [Test coverage additions]
- [Prevention measures]

### Implementation Plan
**Phase 1: Immediate Fix** (Critical path)
- [Action 1]: [Expected time]
- [Action 2]: [Expected time]
- [Validation]: [How to confirm fix works]

**Phase 2: Comprehensive Solution** (Prevention)
- [Test additions]: [Coverage improvements]
- [Monitoring]: [Detection improvements]
- [Documentation]: [Knowledge capture]

**Rollback Plan**:
- [If fix causes issues]
- [How to revert quickly]
- [Alternative approaches ready]

Ready to proceed with implementation?
```

### Exchange 4: Implementation and Testing

**Goal**: Execute fix and validate solution

```
## Bug Fix Implementation

### Implementation Complete
**Changes Made**:
- [File 1]: [Specific changes and reasoning]
- [File 2]: [Specific changes and reasoning]
- [Configuration]: [Any config changes]

### Testing Results
**Unit Tests**:
- [New tests added]: [What they verify]
- [Existing tests]: [Status and any changes]
- [Edge cases]: [Additional scenarios tested]

**Integration Testing**:
- [End-to-end verification]: [Full flow testing]
- [Regression testing]: [Ensuring no new issues]
- [Performance impact]: [Any performance changes]

**Reproduction Test**:
- [Original issue]: ✓ Fixed / ⚠ Still investigating
- [Edge cases]: [Results for related scenarios]
- [Different environments]: [Consistency verification]

### Validation Against Original Problem
**Original symptoms** (from Exchange 1):
- [Symptom 1]: ✓ Resolved
- [Symptom 2]: ✓ Resolved
- [Error messages]: ✓ No longer occurring

**Success Criteria Met**:
- [Criterion 1]: ✓ Verified
- [Criterion 2]: ✓ Verified
```

### Exchange 5: Comprehensive Validation and Monitoring

**Goal**: Ensure fix is robust and monitoring is in place

```
## Comprehensive Fix Validation

### Extended Testing Results
**User Scenario Testing**:
- [User workflow 1]: ✓ Working correctly
- [User workflow 2]: ✓ Working correctly
- [Edge case workflows]: ✓ Handled properly

**Environment Validation**:
- [Local environment]: ✓ Fix verified
- [Staging environment]: ✓ Fix verified
- [Production readiness]: ✓ Ready for deployment

### Monitoring and Prevention
**New Monitoring Added**:
- [Metric 1]: [What it detects]
- [Metric 2]: [What it detects]
- [Alerting]: [When team gets notified]

**Documentation Updated**:
- [Troubleshooting guide]: [How to diagnose similar issues]
- [Runbook updates]: [Operational procedures]
- [Knowledge base]: [Lessons learned capture]

### Post-Fix Analysis
**Why This Happened**:
- [Process gap]: [What allowed this to occur]
- [Testing gap]: [What testing would have caught this]
- [Monitoring gap]: [How to detect this faster]

**Prevention Measures**:
- [Process improvement]: [Changes to prevent recurrence]
- [Automated testing]: [New test coverage]
- [Code review focus]: [What to watch for]
```

### Exchange 6: Documentation and Session Closure

**Goal**: Complete documentation and establish monitoring

```
## Bug Fix Documentation & Closure

### Fix Summary
**Issue**: [Original problem from Exchange 1]
**Root Cause**: [Technical cause identified]
**Solution**: [What was implemented]
**Validation**: [How success was confirmed]

### Implementation Details
**Files Changed**:
- [File listing with change summaries]
- [Configuration changes]
- [Database changes if any]

**Tests Added**:
- [Test descriptions and coverage]
- [Regression prevention tests]

### Operational Impact
**Deployment Notes**:
- [Any special deployment considerations]
- [Rollback procedures if needed]
- [Post-deployment verification steps]

**Monitoring**:
- [New metrics and alerts]
- [Dashboard updates]
- [Log analysis improvements]

### Knowledge Capture
**Lessons Learned**:
- [Technical insights gained]
- [Process improvements identified]
- [Prevention strategies for similar issues]

**Documentation Created/Updated**:
- [Troubleshooting guides]
- [Architecture documentation]
- [Operational runbooks]

### Session Metrics
- **Resolution Time**: [Actual vs estimated]
- **Exchange Count**: [Actual vs target 4-6]
- **Root Cause Accuracy**: [Initial hypothesis vs actual]
- **Fix Effectiveness**: [Complete resolution achieved]

**Session Complete**: Issue resolved with comprehensive prevention measures in place.
```

## Efficiency Optimization Techniques

### Information Capture Strategy

- **Comprehensive Symptoms**: Gather all manifestations upfront
- **Environmental Matrix**: Complete context in Exchange 1
- **Timeline Correlation**: Link symptoms to recent changes
- **Impact Quantification**: Full business context upfront

### Diagnostic Acceleration

- **Hypothesis-Driven**: Form theories based on initial context
- **Parallel Investigation**: Multiple diagnostic paths simultaneously
- **Evidence-Based**: Require proof for all conclusions
- **Systematic Elimination**: Rule out possibilities methodically

### Common Pitfalls to Avoid

- Starting with incomplete problem description
- Investigating symptoms instead of root causes
- Fixing symptoms without addressing underlying issues
- Missing environmental context that affects reproduction
- Implementing fixes without comprehensive testing
- Skipping prevention measures for future occurrences

## Success Metrics

- **Exchange Count**: Target 4-6, Maximum 8
- **Reproduction Success**: 100% on first attempt
- **Root Cause Accuracy**: >90% initial hypothesis accuracy
- **Fix Effectiveness**: 100% issue resolution
- **Prevention Quality**: Comprehensive measures to prevent recurrence

## Session Adaptation

### High Complexity Issues

If issue requires more than 6 exchanges:

- **Break Down**: Separate immediate fix from comprehensive solution
- **Prioritize**: Address critical symptoms first
- **Parallel Track**: Investigation and temporary mitigation simultaneously

### Intermittent Issues

Special handling for hard-to-reproduce problems:

- **Extended Context**: Gather longer timeline of occurrences
- **Pattern Analysis**: Look for correlations in timing/conditions
- **Monitoring First**: Implement detection before attempting fix

### Multiple Root Causes

When investigation reveals compound issues:

- **Prioritize Impact**: Address highest-impact cause first
- **Sequential Resolution**: Fix primary, then secondary causes
- **Comprehensive Testing**: Validate each fix independently

Remember: Bug fixes require thorough investigation and comprehensive solutions. Rushing the diagnostic phase often leads to incomplete fixes and recurring issues.
