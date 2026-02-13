# Dashboard Application Display Issue - FIXED

## Problem Identified

The application "ai-costminimizer" was added to the `applications` table but does NOT appear in the dashboard.

## Root Cause

The dashboard loads applications using a query that requires BOTH:
1. An entry in the `applications` table ✅ (exists)
2. An entry in the `user_applications` table ❌ (MISSING)

### Current Query (src/routes/main_routes.py, line 30-37):
```sql
SELECT a.id, a.name, ua.url, a.description, a.git_url, a.git_local_url, a.git_repo_size, 
       a.docker_build_duration, a.docker_start_duration, a.docker_stop_duration, a.docker_ps_duration,
       d.swautomorph_url
FROM applications a
JOIN user_applications ua ON a.id = ua.application_id  -- INNER JOIN requires match
LEFT JOIN deployments d ON d.user_id = %s AND d.application_name = a.name
WHERE ua.user_id = %s
ORDER BY a.name
```

The `JOIN user_applications` means only applications assigned to users will appear.

## Solution

You need to add an entry to the `user_applications` table to assign "ai-costminimizer" to a user.

### SQL Fix (Run this in your PostgreSQL database):

```sql
-- First, get the application ID
SELECT id, name FROM applications WHERE name = 'ai-costminimizer';

-- Then, assign it to the admin user (or any user)
-- Replace <app_id> with the actual ID from above
-- Replace <user_id> with the target user's ID (typically 1 for admin)

INSERT INTO user_applications (user_id, application_id, url)
VALUES (
    1,  -- admin user_id (adjust if needed)
    (SELECT id FROM applications WHERE name = 'ai-costminimizer'),
    'http://ai-costminimizer.swautomorph.com'  -- adjust URL as needed
);
```

### Alternative: Assign to ALL existing users

```sql
-- Assign ai-costminimizer to all users
INSERT INTO user_applications (user_id, application_id, url)
SELECT 
    u.id,
    a.id,
    'http://ai-costminimizer.swautomorph.com'
FROM users u
CROSS JOIN applications a
WHERE a.name = 'ai-costminimizer'
AND NOT EXISTS (
    SELECT 1 FROM user_applications ua 
    WHERE ua.user_id = u.id AND ua.application_id = a.id
);
```

## Verification

After running the SQL, refresh the dashboard and "ai-costminimizer" should appear.

## Why This Happens

The platform uses a multi-tenant architecture where:
- `applications` table = global application registry
- `user_applications` table = per-user application assignments
- This allows different users to see different applications

When you manually add an application to the database, you must ALSO create the user assignment.

## Recommendation

When adding applications manually, always:
1. Insert into `applications` table
2. Insert into `user_applications` table for each user who should see it
