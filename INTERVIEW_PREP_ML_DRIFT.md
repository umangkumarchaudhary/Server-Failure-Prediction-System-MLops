# 🎓 ML Drift & Monitoring - Interview Preparation Guide

## 1. What are we solving with Drift Detection?
**Q: Why do we need model monitoring?**
**A:** We solve the **"Silent Failure"** problem. Unlike traditional software that crashes when broken (404/500 errors), ML models fail silently—they continue to output predictions, but those predictions become wrong over time because the world changes.

**Q: What are the three main types of drift?**
1.  **Data Drift (Covariate Shift)**: The input data changes.
    *   *Example*: A model trained on summer data (30-40°C) suddenly sees winter inputs (0-10°C).
2.  **Prediction Drift**: The model's output distribution changes significantly.
    *   *Example*: Normally 5% of machines fail. Suddenly, the model predicts 50% failures.
3.  **Concept Drift**: The relationship between input and target changes.
    *   *Example*: Same user behavior that meant "Fraud" last year now means "Legit" this year. (Requires ground truth labels to detect).

---

## 2. What is Evidently AI?
**Q: What is Evidently?**
**A:** It is an open-source Python library used to **analyze and monitor machine learning models**. It calculates statistical metrics to compare a **Reference Dataset** (training data) against a **Current Dataset** (production data) to detect drift and data quality issues.

---

## 3. How does it work mathematically? ("Under the Hood")

### The Core Logic: "Bucketing"
Evidently aligns two datasets:
1.  **Reference (Truth)**: Your training data.
2.  **Current (Live)**: Your production data.

It takes the Reference data and slices it into **bins** (buckets). It then forces the Current data into those exact same bins to compare densities.

### Algorithm 1: Population Stability Index (PSI)
*   **Best for**: Financial/Risk models, general distribution shift.
*   **Formula**:
    $$PSI = \sum ((\%Curr - \%Ref) \times \ln(\frac{\%Curr}{\%Ref}))$$
*   **Intuition**: Measures "How much mass has moved?"
    *   **0**: No change.
    *   **< 0.1**: Safe (Green ✅).
    *   **0.1–0.2**: Warning (Yellow ⚠️).
    *   **> 0.2**: Critical Drift (Red 🚨).

### Algorithm 2: Kolmogorov-Smirnov (KS) Test
*   **Best for**: Numerical data (Sensor readings, continuous values).
*   **The Simple Analogy**:
    Imagine you have two piles of books (Last Week's data vs Today's data) and you stack them by height (shortest to tallest).
    *   **The CDF**: Imagine drawing a line on the wall tracing the top of the stack as you add books. It goes from 0% height to 100%.
*   **The "Gap" ($D$)**:
    You compare the "shape" of Last Week's stack vs Today's stack.
    *   **$D = \max | CDF_{ref} - CDF_{curr} |$**
    *   This measures the **maximum vertical distance** between the two lines.
*   **Intuition**:
    *   If the lines overlap perfectly ($D \approx 0$), the data is the same.
    *   If one line is far above the other (e.g., Today's engines are running 10° hotter), the gap ($D$) gets big.
    *   **Result**: If $D$ is big enough (P-value < 0.05), Evidently says "Drift Detected!" 🚨

### Algorithm Router (What Evidently Picks)
*   **Small Data (<1000 rows)**: Uses **KS-Test** (sensitive).
*   **Large Data (>1000 rows)**: Uses **Wasserstein Distance** (robust).
*   **Categorical Data**: Uses **Chi-Square Test**.

---

## 4. Other Key Concepts

### Data Leakage
**Q: What is it?**
**A:** Training a model with information that isn't available at inference time.
*   *Example*: Including `deal_closed_date` to predict `will_deal_close`. The date only exists *after* the deal closes.
*   *Detection*: Check if any feature has > 99% correlation with the target.

### Training-Serving Skew
**Q: What is it?**
**A:** When the code/logic used to generate features during training differs from the code in production.
*   *Example*: In training, you fill NaNs with `mean`. In production, you fill with `0`.
*   *Detection*: Compare feature distributions immediately after deployment.
