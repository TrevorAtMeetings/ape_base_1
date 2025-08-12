# Brain System Monitoring Guide
## Hypercare Phase - Priority 1 (Next 1-2 Weeks)

---

## Quick Access
**Dashboard URL**: [/brain/metrics](/brain/metrics)  
**Health Check**: [/brain/health](/brain/health)  
**API Metrics**: [/brain/api/metrics](/brain/api/metrics)

---

## What to Monitor

### 1. Response Times (Target: <200ms)
**Dashboard Location**: Top-left metric card + Operations Performance section

**Key Operations to Watch**:
- `calculate_at_point`: Performance calculations for specific operating points
- `find_best_pumps`: Pump selection algorithm execution
- `generate_chart_data`: Chart generation performance

**Action Thresholds**:
- ✅ **Good**: <200ms average
- ⚠️ **Warning**: 200-500ms average (investigate cache performance)
- ❌ **Critical**: >500ms average (immediate investigation needed)

### 2. Error Rates
**Dashboard Location**: Top metric cards + Recent Errors section

**What to Look For**:
- Sudden spikes in error count
- Repeated errors for same operation
- New error types not seen before

**Action Thresholds**:
- ✅ **Good**: <10 errors/hour
- ⚠️ **Warning**: 10-50 errors/hour
- ❌ **Critical**: >50 errors/hour

### 3. Cache Performance
**Dashboard Location**: Cache Hit Rate metric card

**Target**: >50% hit rate

**If Cache Hit Rate is Low**:
- Check if cache is being properly populated
- Review cache key generation logic
- Consider increasing cache size limits

### 4. Discrepancy Tracking
**Dashboard Location**: Discrepancies metric card + Recent Discrepancies section

**Expected Behavior**:
- ~23.5% discrepancy rate is NORMAL (Brain's stricter criteria)
- Monitor for unexpected patterns or new types of discrepancies

---

## User Feedback Collection

### How to Use Feedback Form
Located at the bottom of the monitoring dashboard

1. **When to Submit Feedback**:
   - User reports incorrect pump selection
   - Performance calculation seems wrong
   - Chart displays incorrect data
   - Any unexpected behavior

2. **Information to Include**:
   - Pump Code (if applicable)
   - Issue Type (Selection/Performance/Chart/Other)
   - Detailed description of the issue

3. **What Happens Next**:
   - Feedback is logged with timestamp
   - Appears in Brain metrics for analysis
   - Used to validate Brain's improved logic

---

## Daily Monitoring Checklist

### Morning Check (5 minutes)
- [ ] Open dashboard: `/brain/metrics`
- [ ] Verify all health checks are green
- [ ] Check average response times <200ms
- [ ] Review any overnight errors
- [ ] Note any unusual discrepancy patterns

### Midday Check (2 minutes)
- [ ] Quick glance at response time trend
- [ ] Verify no error spikes
- [ ] Check cache hit rate >50%

### End of Day Review (10 minutes)
- [ ] Review all user feedback submitted
- [ ] Analyze any performance degradation patterns
- [ ] Document any issues for investigation
- [ ] Check total operation counts for usage patterns

---

## Common Issues & Solutions

### Issue: Slow Response Times
**Symptoms**: Operations taking >200ms consistently

**Investigation Steps**:
1. Check specific operation performance: `/brain/api/performance/{operation_name}`
2. Review cache hit rates
3. Check database query performance
4. Monitor for memory issues

**Solutions**:
- Increase cache TTL if appropriate
- Optimize database queries
- Review calculation algorithms for efficiency

### Issue: High Error Rate
**Symptoms**: >10 errors/hour

**Investigation Steps**:
1. Check Recent Errors section for patterns
2. Review error types and operations
3. Check for data quality issues
4. Verify external dependencies (database, etc.)

**Solutions**:
- Add better error handling for edge cases
- Improve data validation
- Fix specific calculation bugs

### Issue: Low Cache Hit Rate
**Symptoms**: Cache hit rate <50%

**Investigation Steps**:
1. Check if cache is being populated
2. Review cache key generation
3. Monitor cache eviction patterns
4. Check for cache invalidation issues

**Solutions**:
- Adjust cache TTL settings
- Improve cache key strategy
- Increase cache size limits

---

## Escalation Path

### Level 1: Self-Service (0-5 minutes)
- Check dashboard for obvious issues
- Review recent errors and discrepancies
- Verify all health checks

### Level 2: Investigation (5-30 minutes)
- Analyze specific operation performance
- Review user feedback patterns
- Check system logs for detailed errors

### Level 3: Code Changes (30+ minutes)
- Debug specific Brain calculations
- Optimize performance bottlenecks
- Fix identified bugs

---

## Success Metrics for Hypercare Phase

### Week 1 Goals
- [ ] Maintain <200ms average response time
- [ ] Keep error rate <10/hour
- [ ] Achieve >50% cache hit rate
- [ ] Collect at least 10 user feedback items
- [ ] Zero critical failures

### Week 2 Goals
- [ ] Improve response times by 10%
- [ ] Reduce error rate to <5/hour
- [ ] Achieve >70% cache hit rate
- [ ] Validate Brain's stricter selections through feedback
- [ ] Prepare for legacy code cleanup

---

## Next Steps After Hypercare

Once stability is confirmed (end of Week 2):

1. **Begin Legacy Code Cleanup** (Priority 2)
   - Remove shadow mode infrastructure
   - Delete legacy calculation functions
   - Simplify codebase

2. **Plan Innovation Features** (Priority 3)
   - What-if Scenario Engine
   - Advanced ML integration
   - Predictive maintenance features

---

## Quick Commands

### Check Brain Status
```bash
curl http://localhost:5000/brain/health
```

### Get Current Metrics
```bash
curl http://localhost:5000/brain/api/metrics | python -m json.tool
```

### Test Specific Operation
```bash
curl http://localhost:5000/brain/api/performance/calculate_at_point
```

---

**Remember**: The 76.5% match rate represents Brain's success, not a limitation. The remaining 23.5% are cases where Brain correctly rejects marginal pumps that Legacy incorrectly accepts.