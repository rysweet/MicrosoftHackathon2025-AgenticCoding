# Bug Fix Session Template

**Target Exchanges**: 4-6 exchanges
**Session Type**: Bug Fix

## Phase 1: Diagnostic Front-Loading (Exchange 1-2)

### Complete Problem Analysis (Exchange 1)
**Gather ALL diagnostic information immediately:**

1. **Bug Reproduction**
   - Exact steps to reproduce the issue
   - Consistent reproduction rate (always/sometimes/rare)
   - Environment details (OS, versions, configuration)
   - Sample inputs that trigger the bug

2. **Current vs Expected Behavior**
   - What exactly is happening (wrong behavior)
   - What should happen instead (expected behavior)
   - Impact scope (who/what is affected)
   - Workarounds currently in use

3. **System Context**
   - When did this start occurring?
   - What recent changes might be related?
   - What components/systems are involved?
   - Any error messages or logs available?

### Root Cause Identification (Exchange 2)
- **Code Analysis**: Identify the problematic code section
- **Data Analysis**: Check for data-related issues
- **Configuration Review**: Verify configuration settings
- **Dependency Check**: Validate third-party component issues

## Phase 2: Fix Implementation (Exchange 3-4)

### Solution Design
- **Fix Strategy**: How to address the root cause
- **Impact Assessment**: What other code might be affected
- **Testing Strategy**: How to verify the fix works
- **Regression Prevention**: How to prevent this bug in future

### Implementation
- **Code Changes**: Minimal, targeted fixes
- **Test Updates**: Add tests to prevent regression
- **Documentation**: Update relevant documentation

## Phase 3: Validation & Deployment (Exchange 5-6)

### Fix Verification
- **Original Bug**: Verify original issue is resolved
- **Regression Testing**: Ensure nothing else broke
- **Edge Cases**: Test boundary conditions
- **Performance Impact**: Verify no performance degradation

### Deployment
- **Code Review**: Quick focused review
- **Deployment Plan**: How to roll out the fix
- **Monitoring**: How to verify fix in production

## Success Criteria

**Bug Fix Complete When**:
- ✅ Original bug no longer reproduces
- ✅ All existing tests still pass
- ✅ New regression tests added
- ✅ Code reviewed and approved
- ✅ No performance degradation
- ✅ Documentation updated
- ✅ Ready for production deployment

## Efficiency Optimizations

### Diagnostic Speed
- **Reproduction First**: Always reproduce before analyzing
- **Log Gathering**: Collect all relevant logs immediately
- **Environment Duplication**: Match production environment
- **Minimal Test Case**: Simplest case that reproduces issue

### Context Preservation
- **Bug Report**: Complete documentation of the issue
- **Fix Rationale**: Why this solution was chosen
- **Alternative Approaches**: What else was considered
- **Future Prevention**: How to avoid similar issues

### Risk Mitigation
- **Regression Risk**: Comprehensive testing strategy
- **Deployment Risk**: Rollback plan if issues arise
- **Performance Risk**: Monitoring and validation

This template ensures rapid bug resolution through front-loaded diagnosis and targeted fixing.