#!/usr/bin/env python3

import sqlite3
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import DB_PATH

def debug_billing_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=== BILLING ACTIVITIES DEBUG ===")
    
    # Check if tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%billing%'")
    tables = cursor.fetchall()
    print(f"Billing-related tables: {tables}")
    
    # Check billing activities
    cursor.execute("""
        SELECT ba.id, u.username, a.name, ba.action, ba.cost_amount, ba.duration_seconds,
               ba.created_at, strftime('%Y-%m', ba.created_at) as month_str
        FROM billing_activities ba
        JOIN users u ON ba.user_id = u.id
        JOIN applications a ON ba.application_id = a.id
        ORDER BY ba.created_at DESC
        LIMIT 20
    """)
    
    activities = cursor.fetchall()
    print(f"\nFound {len(activities)} recent billing activities:")
    
    for activity in activities:
        print(f"ID: {activity[0]}, User: {activity[1]}, App: {activity[2]}, Action: {activity[3]}")
        print(f"  Cost: ${activity[4]}, Duration: {activity[5]}s, Date: {activity[6]}, Month: {activity[7]}")
        print()
    
    # Check for December 2025 activities specifically
    cursor.execute("""
        SELECT ba.id, u.username, a.name, ba.action, ba.cost_amount, ba.duration_seconds,
               ba.created_at
        FROM billing_activities ba
        JOIN users u ON ba.user_id = u.id
        JOIN applications a ON ba.application_id = a.id
        WHERE strftime('%Y-%m', ba.created_at) = '2025-12'
        ORDER BY ba.created_at DESC
    """)
    
    dec_activities = cursor.fetchall()
    print(f"\nDecember 2025 activities: {len(dec_activities)}")
    
    total_cost = 0
    for activity in dec_activities:
        cost = activity[4] if activity[4] else 0
        total_cost += cost
        print(f"User: {activity[1]}, App: {activity[2]}, Cost: ${cost}, Date: {activity[6]}")
    
    print(f"\nTotal cost for December 2025: ${total_cost}")
    
    # Check invoicing table
    cursor.execute("SELECT * FROM invoicing ORDER BY created_at DESC LIMIT 10")
    invoices = cursor.fetchall()
    print(f"\nExisting invoices: {len(invoices)}")
    for invoice in invoices:
        print(f"Invoice ID: {invoice[0]}, User ID: {invoice[1]}, Month: {invoice[2]}, Amount: ${invoice[3]}, Status: {invoice[4]}")
    
    conn.close()

if __name__ == "__main__":
    debug_billing_data()