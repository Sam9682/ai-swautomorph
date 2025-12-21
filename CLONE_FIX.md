# Fix for CLONE Button Issue

## Problem
When the CLONE button is clicked, no progress window is displayed and the API returns error "Application not deployed. Clone first."

## Root Cause
The clone action in the API (`/api/deployments`) is not using streaming response by default, which means the progress window doesn't show up. The clone operation completes in the background but the user doesn't see any feedback.

## Solution
The clone action needs to use streaming response (stream=true) to show real-time progress to the user.

## Changes Required

### File: `/home/ubuntu/ai-swautomorph/src/routes/api_routes.py`

The clone action should support streaming just like start/stop actions. The current code at line ~520 handles clone but doesn't stream the output properly.

Change needed: Make the clone action return streaming response when `stream=true` is set in the request.

### Current Flow:
1. User clicks CLONE button
2. JavaScript calls `deploy_sh_executionCmdInApp()` with action='clone'
3. API receives request with `stream: true`
4. Clone executes but returns JSON response instead of streaming
5. No progress window shown

### Fixed Flow:
1. User clicks CLONE button
2. JavaScript calls `deploy_sh_executionCmdInApp()` with action='clone'
3. API receives request with `stream: true`
4. Clone executes with streaming response
5. Progress window shows real-time output
6. Modal shows final result

## Implementation

The clone action should be modified to support streaming similar to how start/stop/restart actions work.

Add streaming support for clone action by wrapping the git clone operation in a streaming generator function.
