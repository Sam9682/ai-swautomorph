#!/bin/bash
# Quick SQLite Database Recovery for AI-SwAutoMorph

DB_PATH="/home/ubuntu/ai-swautomorph/softfluid/db/ai-swautomorph.db"
BACKUP_PATH="${DB_PATH}.backup_$(date +%Y%m%d_%H%M%S)"

echo "=== SQLite Database Recovery ==="

# Stop the application first
echo "Stopping application..."
pkill -f "python.*ControlPlanFlaskApp.py" 2>/dev/null || true

# Create backup
echo "Creating backup..."
cp "$DB_PATH" "$BACKUP_PATH"
echo "Backup created: $BACKUP_PATH"

# Method 1: SQLite .recover (most effective)
echo "Attempting recovery with .recover command..."
sqlite3 "$DB_PATH" ".recover" | sqlite3 "${DB_PATH}.recovered"

if [ -f "${DB_PATH}.recovered" ]; then
    echo "Recovery successful!"
    mv "$DB_PATH" "${DB_PATH}.corrupted"
    mv "${DB_PATH}.recovered" "$DB_PATH"
    echo "Database restored. Starting application..."
    cd /home/ubuntu/ai-swautomorph && python3 ControlPlanFlaskApp.py &
    exit 0
fi

# Method 2: Dump and restore
echo "Trying dump method..."
sqlite3 "$DB_PATH" ".dump" > "${DB_PATH}.sql" 2>/dev/null
if [ -s "${DB_PATH}.sql" ]; then
    sqlite3 "${DB_PATH}.new" < "${DB_PATH}.sql"
    mv "$DB_PATH" "${DB_PATH}.corrupted"
    mv "${DB_PATH}.new" "$DB_PATH"
    echo "Database recovered with dump method!"
    cd /home/ubuntu/ai-swautomorph && python3 ControlPlanFlaskApp.py &
    exit 0
fi

# Method 3: Reinitialize (last resort)
echo "Recovery failed. Reinitializing database..."
mv "$DB_PATH" "${DB_PATH}.corrupted"
cd /home/ubuntu/ai-swautomorph
python3 ./scripts/cli.py init-db
echo "Database reinitialized. You'll need to re-register users."
python3 ControlPlanFlaskApp.py &