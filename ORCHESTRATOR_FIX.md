# Orchestrator Service Creation Fix

## Issues Identified

When creating a service through the dashboard's "Create Service" button, the following issues occurred:

1. **Null "Desired" Value**: The dashboard showed "Desired: null" instead of the selected replica count (e.g., 1)
2. **Zero "Running" Count**: The dashboard showed "Running: 0" even after successful deployment
3. **Missing Instance Records**: No records were inserted into the `instances` table after `deployApp.sh start` execution
4. **Missing Billing Activities**: No billing activity records were created for the START action

## Root Cause

The `orchestrator_routes.py` file's `create_service()` function was:
1. Creating the service record in the database
2. Executing `deployApp.sh start` via SSH
3. **BUT** not creating instance records after successful deployment
4. **AND** not recording billing activities

The `deployApp.sh` script itself doesn't insert into the `instances` table - it only manages Docker containers. The orchestrator is responsible for tracking instances in the database.

## Solution Implemented

Modified `/home/ubuntu/ai-swautomorph/src/routes/orchestrator_routes.py` in the `create_service()` function to:

### 1. Create Instance Records After Successful Deployment

After `deployApp.sh start` completes successfully (returncode == 0), the code now:
- Finds available ports on the target server
- Creates instance records in the `instances` table for each desired replica
- Sets status to 'running' and health_status to 'healthy'
- Generates unique instance IDs (e.g., "MyApp-replica-1", "MyApp-replica-2")

```python
# Create instance record for each desired replica
for i in range(desired_replicas):
    instance_id = f"{name}-replica-{i+1}"
    cursor.execute('''
        INSERT INTO instances 
        (service_name, instance_id, server_id, status, port, health_status)
        VALUES (%s, %s, %s, 'running', %s, 'healthy')
    ''', (name, instance_id, server_id, port + i))
```

### 2. Record Billing Activity

After creating instance records, the code now:
- Calls `record_billing_activity(user_id, name, 'START')`
- This creates a billing_activities record with:
  - user_id
  - application_id
  - action = 'START'
  - started_at = CURRENT_TIMESTAMP

```python
# Record billing activity for START action
from .billing_routes import record_billing_activity
record_billing_activity(user_id, name, 'START')
```

## Expected Behavior After Fix

1. **Dashboard Display**: 
   - "Desired: 1" (or whatever number was selected)
   - "Running: 1" (matching the number of instances created)

2. **Database State**:
   - `services` table: Contains service record with correct `desired_replicas`
   - `instances` table: Contains instance records for each replica
   - `billing_activities` table: Contains START activity record

3. **Billing Tracking**:
   - START action is recorded with timestamp
   - When service is stopped, STOP action will be recorded
   - Duration and cost will be calculated

## Testing

To verify the fix:

1. **Create a Service**:
   - Go to Orchestrator section
   - Click "Create Service"
   - Select an application and git URL
   - Set desired replicas to 1
   - Click "Create Service"

2. **Check Dashboard**:
   - Services section should show:
     - Desired: 1
     - Running: 1
     - Healthy: 1

3. **Verify Database**:
   ```sql
   -- Check service record
   SELECT * FROM services WHERE name = 'YourAppName';
   
   -- Check instance records
   SELECT * FROM instances WHERE service_name = 'YourAppName';
   
   -- Check billing activities
   SELECT * FROM billing_activities WHERE application_id = (
       SELECT id FROM applications WHERE name = 'YourAppName'
   );
   ```

## Additional Notes

- The fix maintains backward compatibility with existing services
- Error handling is in place - if instance creation fails, it's logged but doesn't prevent service creation
- The billing activity recording is also wrapped in try-catch to prevent failures from blocking service creation
- Port allocation is automatic and sequential (8000, 8001, 8002, etc.)

## Files Modified

- `/home/ubuntu/ai-swautomorph/src/routes/orchestrator_routes.py`
  - Function: `create_service()`
  - Lines: Added instance creation and billing activity recording after successful deployment
