import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import uuid
import os

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Configuration
NUM_USERS = 10000
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2023, 12, 31)

# Probabilities & Distributions
CITIES = ["Delhi", "Mumbai", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Pune"]
CITY_PROBS = [0.2, 0.2, 0.15, 0.15, 0.1, 0.1, 0.1]
DEVICE_TYPES = ["Android", "iOS"]
DEVICE_PROBS = [0.8, 0.2] # 80% Android
EVENTS = ["login", "level_start", "level_complete", "purchase"]

# Generate data directories if not exist
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

def random_date(start, end):
    """Generate a random datetime between `start` and `end`."""
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = random.randrange(int_delta)
    return start + timedelta(seconds=random_second)

print("Starting data generation for Mobile Game Analytics (India-Focused)...")

# 1. Generate Users Table
print("Generating Users...")
users = []
paying_user_ids = set()

for _ in range(NUM_USERS):
    user_id = str(uuid.uuid4())
    install_date = random_date(START_DATE, END_DATE)
    city = np.random.choice(CITIES, p=CITY_PROBS)
    device = np.random.choice(DEVICE_TYPES, p=DEVICE_PROBS)
    
    users.append({
        "user_id": user_id,
        "install_date": install_date.strftime("%Y-%m-%d %H:%M:%S"),
        "city": city,
        "device_type": device
    })
    
    # Decide if user is a paying user (approx 4%)
    if random.random() < 0.04:
        paying_user_ids.add(user_id)

users_df = pd.DataFrame(users)
users_df['install_date'] = pd.to_datetime(users_df['install_date'])

# 2. Generate Sessions and Events Tables
print("Generating Sessions and Events...")
sessions = []
events = []
transactions = []

# Distribute max days the user stayed active (High Early Churn)
# Weibull or Exponential distribution is good for churn
# Most users leave within 1-3 days, very few stay for > 30 days
for idx, user in users_df.iterrows():
    u_id = user['user_id']
    inst_date = user['install_date']
    
    # Calculate days active (gamma or exponential distribution to simulate high early churn)
    # Most will have 0-3 days, a long tail will reach 30-100+
    days_active = int(np.random.exponential(scale=5))
    days_active = min(days_active, (END_DATE - inst_date).days)
    
    if days_active == 0:
        num_sessions = np.random.randint(1, 3) # Even churned users have at least 1 session
    else:
        num_sessions = np.random.randint(1, 3) * days_active
    
    current_time = inst_date
    current_level = 1
    
    for _ in range(num_sessions):
        # Time gap between sessions
        gap_hours = np.random.exponential(scale=24)
        current_time += timedelta(hours=gap_hours)
        
        if current_time > END_DATE:
            break
            
        session_id = str(uuid.uuid4())
        session_duration = np.random.exponential(scale=10) + 1 # minutes
        
        sessions.append({
            "session_id": session_id,
            "user_id": u_id,
            "session_date": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "session_duration_minutes": round(session_duration, 2)
        })
        
        # Events per session
        # Always login
        events.append({
            "event_id": str(uuid.uuid4()),
            "user_id": u_id,
            "event_type": "login",
            "event_time": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "level_number": current_level
        })
        
        # Play levels
        num_levels_played = np.random.randint(1, 5)
        for i in range(num_levels_played):
            # level start
            level_time = current_time + timedelta(minutes=i*2)
            events.append({
                "event_id": str(uuid.uuid4()),
                "user_id": u_id,
                "event_type": "level_start",
                "event_time": level_time.strftime("%Y-%m-%d %H:%M:%S"),
                "level_number": current_level
            })
            
            # level complete (70% win rate)
            if random.random() < 0.7:
                events.append({
                    "event_id": str(uuid.uuid4()),
                    "user_id": u_id,
                    "event_type": "level_complete",
                    "event_time": (level_time + timedelta(minutes=1.5)).strftime("%Y-%m-%d %H:%M:%S"),
                    "level_number": current_level
                })
                current_level += 1
                
        # Purchases within session for paying users
        if u_id in paying_user_ids and random.random() < 0.15: # 15% chance to buy something in a session
            # INR amounts: 10 to 500 common, rare up to 2000
            if random.random() < 0.9:
                amount = np.random.choice([10, 25, 50, 99, 149, 199, 299, 499])
            else:
                amount = np.random.choice([999, 1499, 1999])
                
            purchase_time = current_time + timedelta(minutes=session_duration / 2)
            
            # Add transaction event
            events.append({
                "event_id": str(uuid.uuid4()),
                "user_id": u_id,
                "event_type": "purchase",
                "event_time": purchase_time.strftime("%Y-%m-%d %H:%M:%S"),
                "level_number": current_level
            })
            
            # Add to transactions table
            transactions.append({
                "transaction_id": str(uuid.uuid4()),
                "user_id": u_id,
                "amount_inr": amount,
                "purchase_time": purchase_time.strftime("%Y-%m-%d %H:%M:%S")
            })

print("Formatting dataframes...")
sessions_df = pd.DataFrame(sessions)
events_df = pd.DataFrame(events)
transactions_df = pd.DataFrame(transactions)

print("Saving to CSV...")
users_df.to_csv(os.path.join(DATA_DIR, "users.csv"), index=False)
sessions_df.to_csv(os.path.join(DATA_DIR, "sessions.csv"), index=False)
events_df.to_csv(os.path.join(DATA_DIR, "events.csv"), index=False)
transactions_df.to_csv(os.path.join(DATA_DIR, "transactions.csv"), index=False)

print(f"Dataset summary:")
print(f"Users: {len(users_df)}")
print(f"Sessions: {len(sessions_df)}")
print(f"Events: {len(events_df)}")
print(f"Transactions: {len(transactions_df)}")
print(f"Data generation complete! Files saved in: {os.path.abspath(DATA_DIR)}")
