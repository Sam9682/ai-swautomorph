# Database Recovery S3 Feature

## Overview
Modified the `recover_database()` function in `deployControlPlan.sh` to allow customers to select backups from either local storage or the remote S3 bucket.

## Changes Made

### 1. Backup Source Selection
Added an interactive menu at the start of the recovery process that allows users to choose between:
- **Local backups**: `./softfluid/db/backup` (existing behavior)
- **Remote S3 backups**: `s3://softfluid/db/backup` (new feature)

The menu uses `simple-term-menu` for a better user experience, with a fallback to numbered selection.

### 2. S3 Backup Listing
When S3 is selected:
- Checks if AWS CLI is installed
- Lists available backup directories from `s3://softfluid/db/backup/` using the `OVH-SWAUTOMORPH` profile
- Displays the number of backups found
- Provides helpful error messages if AWS CLI is missing or no backups are found

### 3. S3 Backup Download
When a backup from S3 is selected:
- Creates a temporary directory: `./softfluid/db/backup/s3-temp-<backup_name>`
- Downloads the selected backup using `aws s3 sync`
- Provides clear feedback on download progress
- Handles download failures gracefully with cleanup

### 4. Cleanup
After the recovery process completes:
- Automatically removes the temporary S3 backup directory
- Keeps the pre-recovery backup for safety
- Provides clear status messages

## Usage

Run the recovery command as before:
```bash
./deployControlPlan.sh recover_db
```

The script will now prompt you to:
1. Select backup source (Local or S3)
2. Select which backup to restore
3. Proceed with the restoration

## Requirements

For S3 backup recovery:
- AWS CLI must be installed: `sudo apt-get install awscli`
- AWS profile `OVH-SWAUTOMORPH` must be configured
- Network access to S3 bucket `s3://softfluid`

## Benefits

- **Disaster Recovery**: Restore from remote backups if local storage fails
- **Cross-Server Recovery**: Restore backups from one server to another
- **Backup Verification**: Test S3 backups without manual download
- **Flexibility**: Choose the most appropriate backup source for each situation
