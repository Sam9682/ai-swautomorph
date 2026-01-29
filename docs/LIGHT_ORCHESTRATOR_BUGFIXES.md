# Bug Fixes for App Orchestrator

## Issues Fixed

### 1. SSH Host Key Verification Error
**Problem**: SSH command failed with "Host key verification failed"

**Solution**: Added SSH options to disable strict host key checking
- Added `-o StrictHostKeyChecking=no`
- Added `-o UserKnownHostsFile=/dev/null`

**File**: `/home/ubuntu/ai-swautomorph/src/routes/orchestrator_routes.py`

### 2. NoneType Comparison Error in Server Selection
**Problem**: Error "'<' not supported between instances of 'int' and 'NoneType'"

**Root Cause**: `server_capacity_appli_max` field in servers table contained NULL values

**Solutions**:
1. Modified `_select_server()` query to:
   - Use `COALESCE(s.server_capacity_appli_max, 100)` for NULL handling
   - Filter out servers with NULL capacity: `WHERE server_capacity_appli_max IS NOT NULL`
   - Use explicit GROUP BY with capacity field

2. Created migration script to set default values for NULL capacities

**File**: `/home/ubuntu/ai-swautomorph/src/orchestrator.py`

### 3. NULL Port Values Handling
**Problem**: Port field in instances table could contain NULL values causing issues

**Solution**: Modified `_find_available_port()` to:
- Filter NULL ports in query: `AND port IS NOT NULL`
- Filter NULL values when building used_ports set

**File**: `/home/ubuntu/ai-swautomorph/src/orchestrator.py`

## Apply Fixes

```bash
# 1. Fix server capacity NULL values
psql -U swautomorph -d ai_swautomorph -f /home/ubuntu/ai-swautomorph/migration/fix_server_capacity.sql

# 2. Restart application
cd /home/ubuntu/ai-swautomorph && ./deployControlPlan.sh restart
```

## Testing

After applying fixes, test service creation:
1. Login as admin
2. Navigate to App Orchestrator
3. Click "Create Service"
4. Select an application from dropdown
5. Select a git URL from dropdown
6. Set desired replicas
7. Click "Create Service"

Expected result: Service created successfully without SSH or NoneType errors.
