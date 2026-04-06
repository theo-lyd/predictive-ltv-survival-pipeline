# Beginner Walkthrough

## Who This Is For
This guide is for someone who is new to the project and wants to understand what it does, how it is organized, how it would run, and how to reproduce it.

## What the Project Does
The project studies how discounts given at signup affect long-term customer value in a subscription business. It uses a data platform to ingest data, clean it, analyze retention, calculate LTV, and show the results in a dashboard.

## Main Idea in Simple Terms
Think of the system as a refinery:
- Raw data comes in.
- The data is cleaned and checked.
- Analytics are produced.
- Leaders use the outputs to make decisions.

## Project Structure
- Project Brief: what the project is and why it matters.
- Implementation Plan: the step-by-step build process.
- Requirement Spec: the formal rules and requirements.
- Business Blueprint: the executive and management view.

## How It Is Implemented
### Step 1: Setup
Create a repeatable development environment with Codespaces, Python, Java, dbt, and Databricks access.

### Step 2: Ingest Raw Data
Bring in the base churn dataset and synthetic promotion data into the Bronze layer.

### Step 3: Clean the Data
Use dbt, Spark, and Great Expectations to standardize formats, remove duplicates, and validate business rules.

### Step 4: Model the Business Questions
Compute survival curves, customer tenure, discount intensity, and LTV.

### Step 5: Present the Results
Use a dashboard and AI narrative to explain what the data means for management.

## How to Run It
The repository currently contains documentation that defines the intended implementation. A full run would follow this sequence once code and infrastructure are present:
1. Open the repository in Codespaces.
2. Configure secrets for Databricks and any external services.
3. Install dependencies.
4. Run ingestion jobs for Bronze data.
5. Execute dbt and validation jobs for Silver and Gold.
6. Start the dashboard application.

## How to Reproduce the Analysis
1. Use the same source dataset and synthetic generation seed.
2. Re-run ingestion with the same schema and file conventions.
3. Apply the same transformation and business rules.
4. Recompute the Gold metrics and survival outputs.
5. Compare the dashboard results and KPI values.

## What You Need to Understand First
- Bronze means raw data.
- Silver means cleaned and trusted data.
- Gold means final business metrics and predictive outputs.
- LTV is the estimated lifetime value of a customer.
- Churn means the customer leaves or becomes inactive.

## Common Pitfalls
- Treating the synthetic promotions as if they were real production marketing records.
- Confusing correlation with causation.
- Using KPI definitions that differ from the approved business rules.

## End State
If implemented fully, the project becomes a reliable system for understanding whether discount policy is helping the business grow profitably or creating short-lived revenue.
