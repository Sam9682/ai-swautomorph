# Bug Fix: Cloned But Not Compliant Apps Not Showing in Virtual IT Team Dropdown

## Problem
Applications that were cloned but missing `deployApp.sh` (not compliant) were not appearing in the Virtual IT Team "unifiedAppSelect" dropdown, even though they should be visible with the "MAKE App. Compliant" action available.

## Root Cause
The frontend was using a single error message check to determine if an app was "not cloned":
```javascript
const isNotCloned = logs.toLowerCase().includes(APP_NOT_DEPLOYED_MESSAGE.toLowerCase());
// APP_NOT_DEPLOYED_MESSAGE = 'deployApp.sh not found'
```

This caused a problem because the backend returns TWO different error messages:
1. **`"Application not deployed. Clone it first."`** - No deployment record exists (truly not cloned)
2. **`"deployApp.sh not found in {path}"`** - Deployment record exists but deployApp.sh is missing (cloned but not compliant)

The frontend was treating BOTH cases as "not cloned" and hiding them from the Virtual IT Team dropdown.

## Solution
Updated the `updateApplicationButtonStatus()` function to distinguish between the two states:

### Before:
```javascript
const isNotCloned = logs.toLowerCase().includes(APP_NOT_DEPLOYED_MESSAGE.toLowerCase());
```

### After:
```javascript
// Check for truly not cloned
const isNotCloned = logs.toLowerCase().includes('application not deployed') || 
                    logs.toLowerCase().includes('clone it first');

// Check for cloned but missing deployApp.sh
const isClonedButNotCompliant = logs.toLowerCase().includes('deployapp.sh not found');
```

### Logic Flow:
```javascript
if (isClonedButNotCompliant) {
    // App is cloned but missing deployApp.sh
    applicationStatus = 'cloned_but_not_compliant';
} else if (!isNotCloned) {
    // App is cloned and has deployApp.sh - check if running
    // ... check for IS_RUNNING / IS_NOT_RUNNING
} else {
    // Truly not cloned
    applicationStatus = 'is_not_cloned';
}
```

## Behavior After Fix

### Application States:
1. **`is_not_cloned`** - No deployment record
   - Hidden from Virtual IT Team dropdown
   - Shows "Not Cloned" button
   - Only Clone button visible

2. **`cloned_but_not_compliant`** - Deployment exists but missing deployApp.sh
   - **VISIBLE in Virtual IT Team dropdown** ✅
   - Shows "⚠️ Not Compliant" button
   - Actions available: MAKE_COMPLIANT, LOGS
   - Clone button visible (for re-cloning)

3. **`cloned_but_not_running`** - Fully compliant but stopped
   - Visible in Virtual IT Team dropdown
   - Shows "🔴 App is not running" button
   - Actions available: START, LOGS, MODIFY_CODE, SPECIFY

4. **`cloned_and_running`** - Fully compliant and running
   - Visible in Virtual IT Team dropdown
   - Shows "🟢 App is running" button
   - Actions available: STOP, PS, LOGS, MODIFY_CODE, SPECIFY

## Testing
To verify the fix:
1. Clone an application that doesn't have `deployApp.sh`
2. Check the dashboard - app card should show "⚠️ Not Compliant"
3. Open Virtual IT Team panel
4. The application should appear in the dropdown
5. Select it - "MAKE App. Compliant" should be available
6. Select that action - input should fill with the correct message

## Files Modified
- `templates/dashboard.html` - Updated `updateApplicationButtonStatus()` function

## Backend Reference
The error messages come from `src/routes/api_routes.py` in the `_handle_app_action()` function:
- Line ~1314: `'Application not deployed. Clone it first.'`
- Line ~1325: `'deployApp.sh not found in {deploy_script}'`
