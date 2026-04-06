# Power BI Dashboard Instructions
## Mobile Game User Analytics & Growth Dashboard (India-Focused)

Follow these steps to build the interactive Power BI dashboard for the game analytics project.

### 1. Data Connection & Preparation
1. Open Power BI Desktop.
2. Go to **Get Data** > **Text/CSV**.
3. Import the following generated CSV files from the `data/` folder:
   - `users.csv`
   - `sessions.csv`
   - `events.csv`
   - `transactions.csv`
4. **Data Modeling (Relationships):**
   - Head to the **Model View** on the left panel.
   - Connect `users.csv` to `sessions.csv` via `user_id` (1 to Many).
   - Connect `users.csv` to `events.csv` via `user_id` (1 to Many).
   - Connect `users.csv` to `transactions.csv` via `user_id` (1 to Many).
5. **Format Currency:**
   - Go to the **Data View**, click on `transactions` table.
   - Select the `amount_inr` column.
   - Under Column tools, set the **Format** to **Currency** and select the **₹ English (India)** symbol.

---

### 2. Dashboard Layout & Visuals

#### A. KPI Overview (Top Panel)
Format these as **Card** visuals:
- **DAU**: Count of `session_id` from `sessions` (filter with today/last day date).
- **MAU**: Count of `session_id` from `sessions` (filter to current month).
- **Total Revenue (₹)**: Sum of `amount_inr`. (Ensure ₹ symbol is visible).
- **Day 1 Retention**: Create a quick measure comparing install_date to next day's session.

#### B. Funnel Visualization (Installs > Logins > Played > Purchased)
- **Visual Type**: Funnel Chart
- **Category / Values**: Create a measure or use counts from the `events` table:
  1. Total Installs (`COUNT(user_id)` from `users`)
  2. Total Logins (`COUNT(event_id)` where `event_type = 'login'`)
  3. Total Played (`COUNT(event_id)` where `event_type = 'level_start'`)
  4. Total Purchased (`COUNT(transaction_id)`)

#### C. Retention Dashboard
- **Visual Type**: Matrix (Cohort Heatmap)
- **Rows**: Install Month (`users[install_date]`)
- **Columns**: Days Since Install / Month Number (Create a custom column `DATEDIFF(install_date, session_date, MONTH)`)
- **Values**: Distinct count of `user_id` from `sessions` (formatted as % of Grand Total). Use conditional formatting (background color) to create a Heatmap effect.

#### D. Engagement Dashboard
- **Visual Type**: Line Chart (Session duration over time)
  - Axis: `session_date`
  - Values: Average of `session_duration_minutes`
- **Visual Type**: Donut Chart (Active vs Inactive)
  - Values: Count of users with sessions in last 14 days vs completely churned users.

#### E. Revenue Dashboard
- **Visual Type**: Column Chart / Area Chart (Revenue Trends)
  - Axis: `purchase_time` (Month/Week)
  - Values: Sum of `amount_inr`
- **Visual Type**: Pie Chart (Paying vs Non-paying)
  - Value: Distinct count of users in `transactions` vs absolute total users.

#### F. User Segmentation
- **Visual Type**: Scatter Plot
  - X-Axis: Average Session Duration
  - Y-Axis: Total Revenue (₹)
  - Details: `user_id` (To highlight high-value vs low-engagement users)

---

### 3. Slicers / Filters
Add the following interactable slicers at the top or side panel:
- **City Slicer**: Use `city` from `users` (Delhi, Mumbai, Bangalore, Hyderabad, Chennai, Kolkata, Pune).
- **Device Type Slicer**: Use `device_type` from `users` (Android / iOS).
- **Date Range Slicer**: Use `install_date` or `session_date`.

### 4. Aesthetics & Branding
- Apply a dark/blue contrasting theme (gaming style) using **View** > **Themes**.
- Ensure large bold fonts for KPIs.
- Apply subtle shadows and rounded borders to the visual containers.
