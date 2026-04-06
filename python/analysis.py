import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# Setup Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
CHARTS_DIR = os.path.join(DATA_DIR, 'charts')

os.makedirs(CHARTS_DIR, exist_ok=True)

print("Loading datasets...")
try:
    users = pd.read_csv(os.path.join(DATA_DIR, 'users.csv'), parse_dates=['install_date'])
    sessions = pd.read_csv(os.path.join(DATA_DIR, 'sessions.csv'), parse_dates=['session_date'])
    events = pd.read_csv(os.path.join(DATA_DIR, 'events.csv'), parse_dates=['event_time'])
    transactions = pd.read_csv(os.path.join(DATA_DIR, 'transactions.csv'), parse_dates=['purchase_time'])
except FileNotFoundError:
    print("Error: Datasets not found. Please run data_generator.py first.")
    exit()

# ==========================================
# 0. DATA CLEANING & PREPROCESSING
# ==========================================

print("Cleaning data...")
# Fill missing level_number with 0 (for logins/purchases if any missing)
events['level_number'] = events['level_number'].fillna(0)

# Merge datasets for comprehensive analysis
# User + Session df
user_sessions = pd.merge(sessions, users, on='user_id', how='left')

# Drop invalid sessions
user_sessions = user_sessions.dropna(subset=['session_duration_minutes'])

# ==========================================
# 1. EXPLORATORY & ENGAGEMENT ANALYSIS
# ==========================================

print("Running Engagement Analysis...")
# Avg session duration and sessions per user
avg_session_length = sessions['session_duration_minutes'].mean()
sessions_per_user = sessions.groupby('user_id').size().mean()

print(f"Average Session Duration: {avg_session_length:.2f} minutes")
print(f"Average Sessions Per User: {sessions_per_user:.2f}")

# Session distribution Plot
plt.figure(figsize=(10, 6))
sessions['session_duration_minutes'].plot(kind='hist', bins=50, color='skyblue', edgecolor='black')
plt.title('Distribution of Session Duration')
plt.xlabel('Session Duration (Minutes)')
plt.ylabel('Frequency')
plt.grid(axis='y', alpha=0.75)
plt.savefig(os.path.join(CHARTS_DIR, 'session_distribution.png'))
plt.close()

# ==========================================
# 2. RETENTION ANALYSIS (Day 1 & Day 7)
# ==========================================

print("Running Retention Analysis...")
user_sessions['install_date_only'] = user_sessions['install_date'].dt.floor('D')
user_sessions['session_date_only'] = user_sessions['session_date'].dt.floor('D')

# Calculate difference in days
user_sessions['days_since_install'] = (user_sessions['session_date_only'] - user_sessions['install_date_only']).dt.days

# Retention by Day
retention_data = user_sessions.groupby('days_since_install')['user_id'].nunique()
total_users = users['user_id'].nunique()
retention_pct = (retention_data / total_users) * 100

d1_retention = retention_pct.get(1, 0)
d7_retention = retention_pct.get(7, 0)

print(f"Day 1 Retention: {d1_retention:.2f}%")
print(f"Day 7 Retention: {d7_retention:.2f}%")

# Plot Retention Curve (first 30 days)
plt.figure(figsize=(10,6))
retention_pct[retention_pct.index <= 30].plot(marker='o', color='coral')
plt.title('User Retention Curve (First 30 Days)')
plt.xlabel('Days Since Install')
plt.ylabel('Retention (%)')
plt.grid(True)
plt.savefig(os.path.join(CHARTS_DIR, 'retention_curve.png'))
plt.close()

# ==========================================
# 3. CHURN ANALYSIS
# ==========================================

print("Running Churn Analysis...")
# define churn as inactive for 14 days
last_activity_date = sessions['session_date'].max()
churn_cutoff_date = last_activity_date - pd.Timedelta(days=14)

last_user_sessions = sessions.groupby('user_id')['session_date'].max().reset_index()
last_user_sessions['is_churned'] = last_user_sessions['session_date'] < churn_cutoff_date

churn_rate = last_user_sessions['is_churned'].mean() * 100
print(f"Overall Churn Rate (14-day inactivity): {churn_rate:.2f}%")

# ==========================================
# 4. FUNNEL ANALYSIS
# ==========================================

print("Running Funnel Analysis...")
total_installs = len(users)
users_logged_in = events[events['event_type'] == 'login']['user_id'].nunique()
users_played = events[events['event_type'] == 'level_start']['user_id'].nunique()
users_purchased = transactions['user_id'].nunique()

funnel_stages = ['Installs', 'Logins', 'Played Game', 'Made Purchase']
funnel_counts = [total_installs, users_logged_in, users_played, users_purchased]

plt.figure(figsize=(10,6))
plt.bar(funnel_stages, funnel_counts, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
plt.title('User Conversion Funnel')
plt.ylabel('Number of Users')
for i, v in enumerate(funnel_counts):
    plt.text(i, v + 50, f"{v} ({(v/total_installs)*100:.1f}%)", ha='center', fontweight='bold')
plt.savefig(os.path.join(CHARTS_DIR, 'funnel_analysis.png'))
plt.close()

# ==========================================
# 5. REVENUE ANALYSIS
# ==========================================

print("Running Revenue Analysis...")
total_revenue = transactions['amount_inr'].sum()
paying_users = transactions['user_id'].nunique()
conversion_rate = (paying_users / total_users) * 100
arpu = total_revenue / total_users
arppu = total_revenue / paying_users if paying_users > 0 else 0

print(f"Total Revenue (INR): {total_revenue:,.2f}")
print(f"Conversion Rate (Free -> Paid): {conversion_rate:.2f}%")
print(f"ARPU (Average Revenue Per User) (INR): {arpu:.2f}")
print(f"ARPPU (Average Revenue Per Paying User) (INR): {arppu:.2f}")

# Revenue trends over time (monthly)
transactions['month'] = transactions['purchase_time'].dt.to_period('M')
monthly_revenue = transactions.groupby('month')['amount_inr'].sum()

if not monthly_revenue.empty:
    plt.figure(figsize=(10,6))
    monthly_revenue.plot(kind='line', marker='s', color='green')
    plt.title('Monthly Revenue Trend (₹)')
    plt.xlabel('Month')
    plt.ylabel('Revenue (INR)')
    plt.grid(True)
    plt.savefig(os.path.join(CHARTS_DIR, 'revenue_trend.png'))
    plt.close()

# Revenue Distribution plot
plt.figure(figsize=(10,6))
transactions['amount_inr'].plot(kind='hist', bins=20, color='gold', edgecolor='black')
plt.title('Distribution of Purchase Amounts (₹)')
plt.xlabel('Amount (INR)')
plt.ylabel('Frequency')
plt.savefig(os.path.join(CHARTS_DIR, 'revenue_distribution.png'))
plt.close()

# ==========================================
# 6. USER SEGMENTATION
# ==========================================

print("Running User Segmentation...")
# High vs Low Engagement (based on total sessions)
user_session_counts = sessions.groupby('user_id').size()
engagement_threshold = user_session_counts.quantile(0.75) # Top 25% are highly engaged

users_with_sessions = pd.DataFrame(users)
users_with_sessions['total_sessions'] = users_with_sessions['user_id'].map(user_session_counts).fillna(0)

high_engagement = users_with_sessions[users_with_sessions['total_sessions'] >= engagement_threshold]
low_engagement = users_with_sessions[(users_with_sessions['total_sessions'] > 0) & (users_with_sessions['total_sessions'] < engagement_threshold)]

print(f"High Engagement Users (>= {engagement_threshold} sessions): {len(high_engagement)}")
print(f"Low Engagement Users (< {engagement_threshold} sessions): {len(low_engagement)}")
print(f"Paying Users: {paying_users}")

print(f"Analysis complete. Charts saved to {CHARTS_DIR}")
