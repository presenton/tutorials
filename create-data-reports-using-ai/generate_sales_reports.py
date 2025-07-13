import os
import pandas as pd
import requests

os.makedirs('reports', exist_ok=True)

df = pd.read_csv("sales_data.csv")

company_groups = df.groupby("Company")

def build_prompt(company, group):
    """
    Build a markdown prompt with data summary, chart instructions, and slide structure.
    """
    summary = []
    regions = group['Region'].unique()
    total_sales = group['Total Sales'].sum()
    total_clients = group['New Clients'].sum()
    churn = group['Client Churn Rate'].mean()
    satisfaction = group['Customer Satisfaction'].mean()
    growth = group['Growth vs Last Quarter'].mean()
    marketing = group['Marketing Spend'].sum()
    notable = "; ".join(group['Notable Events'].unique())

    # Markdown-structured prompt
    prompt = f"""
## Sales Report for {company}

### 1. Executive Summary
- Total sales: **${total_sales:,.0f}**
- Average client churn: **{churn:.2f}%**
- Customer satisfaction: **{satisfaction:.2f}/10**
- Notable events: _{notable}_

### 2. Regional Performance
**Bar Chart:** Regional Total Sales

| Region | Sales |
|---|---|
"""    
    for region in regions:
        reg_sales = group[group['Region'] == region]['Total Sales'].sum()
        prompt += f"| {region} | ${reg_sales:,.0f} |\n"

    prompt += """

### 3. Product Performance
**Bar Chart:** Sales by Product per Region

| Region | Product A | Product B | Product C |
|---|---|---|---|
"""
    for region in regions:
        gr = group[group['Region'] == region]
        a = gr['Product A Sales'].sum()
        b = gr['Product B Sales'].sum()
        c = gr['Product C Sales'].sum()
        prompt += f"| {region} | ${a:,.0f} | ${b:,.0f} | ${c:,.0f} |\n"

    prompt += f"""

### 4. Key Metrics & Trends
- Aggregate new clients this month: **{total_clients}**
- Mean growth vs last quarter: **{growth:.2f}%**
- Total marketing spend: **${marketing:,.0f}**

### 5. Top Performers
| Region | Top Sales Rep | New Clients |
|---|---|---|
"""
    for region in regions:
        gr = group[group['Region'] == region]
        rep = gr['Top Sales Rep'].iloc[0]
        clients = gr['New Clients'].iloc[0]
        prompt += f"| {region} | {rep} | {clients} |\n"

    prompt += """

---

**Instructions:**
- Create 1 slide per section (5 total).
- Use clean, professional visuals.
- For charts, display the specified bar chart with given data.
- Use summary bullet points before every chart or table for clarity.
**Do exactly as in said here.**
"""

    return prompt

for company, group in company_groups:
    print(f"Generating report for {company}")
    prompt = build_prompt(company, group)
    data = {
        "prompt": prompt,
        "n_slides": "5",
        "language": "English",
        "theme": "light_red",
        "export_as": "pdf"
    }
    response = requests.post(
        "http://localhost:5000/api/v1/ppt/generate/presentation",
        data=data
    )
    if response.ok:
        result = response.json()
        print("Downloading report...")
        download_url = f"http://localhost:5000{result['path']}"
        filename = f"reports/{company}_Sales_Report.pdf"
        file_response = requests.get(download_url)
        if file_response.ok:
            with open(filename, 'wb') as f:
                f.write(file_response.content)
            print(f"Report for {company} saved as {filename}")
        else:
            print(f"Failed to download report for {company}: {file_response.status_code}")
    else:
        print(f"Failed to generate report for {company}: {response.text}")


