# Product Insights Copilot: Groww

Groww AI Product Feedback Intelligence \u0026 Support Workflow is a full-stack application that ingests real Google Play reviews for the Groww Android app, runs an AI-powered analysis pipeline, and produces a Weekly Product Pulse and Customer Fee Explainer.

---

## 🚀 How to Run

### 1. Backend Setup
Navigate to the `backend` directory and start the FastAPI server:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Make sure to configure your .env file with necessary API keys (GROQ_API_KEY, TAVILY_API_KEY, etc.)
uvicorn api.main:app --reload --port 8000
```

### 2. Frontend Setup
Navigate to the `frontend` directory and start the Vite dev server:
```bash
cd frontend
npm install
npm run dev
```

---

## 🔍 What Fee Issue Was Identified From Reviews?
Based on the AI analysis of customer reviews, the primary fee issue identified is **DP (Depository Participant) Charges and AMC (Account Maintenance Charges)**. Many users expressed confusion over unexpected deductions when selling stocks or maintaining their accounts, often mistaking them for hidden platform fees.

---

## 📝 Weekly Product Pulse (Sample)

**Date:** Sept 04, 2026
**Overall Sentiment:** 65% Positive, 25% Neutral, 10% Negative

**Top Themes Identified:**
1. **UI/UX Excellence:** Users consistently praise the clean and intuitive interface.
2. **Onboarding:** Fast KYC processing is a major plus point.
3. **Fee Confusion:** Recurring questions around DP charges on stock delivery.

**Customer Fee Explainer: DP Charges**
- **What is it?** A flat fee charged by the depository (CDSL/NSDL) when shares are debited from your Demat account.
- **How much?** ₹13.5 + GST per company, per day, regardless of the quantity sold.
- **Why?** It covers the cost of maintaining your shares in digital format and facilitating the transfer.

---

## 📎 Notes/Doc Snippet Showing Appended Entry

```markdown
### [Added via Product Insights Copilot - 2026-09-04]
**Weekly Product Pulse \u0026 Support Guidelines**

**Summary:** Continued positive reception of the new UI update. Increased volume of support tickets regarding DP charges on delivery sales.

**Action Item:** Support team to use the approved **Customer Fee Explainer: DP Charges** when responding to queries about "hidden charges" on stock sales.
```

---

## 📧 Email Draft Text

**Subject:** Weekly Product Pulse + Customer Clarification — [DP Charges]

**Body:**
Hi Team,

Here is the Weekly Product Pulse based on recent Play Store reviews. 

**Key Insights:**
- Users love the fast KYC process.
- We noticed a spike in confusion regarding DP charges when users sell their holdings.

**Approved Support Snippet for DP Charges:**
Please use the following explanation for customers confused about recent deductions:
*\"A flat DP (Depository Participant) charge of ₹13.5 + GST is levied by the depository (CDSL) whenever shares are debited from your Demat account. This is a standard industry charge, not a hidden Groww fee, and applies per scrip per day.\"*

Best,
Product Insights Copilot

---

## 💬 Reviews Sample

- *"The app is really smooth and I opened my account in 5 minutes! But yesterday when I sold 10 shares of Tata Motors, I saw an extra charge. What is this hidden fee?"* - ⭐⭐⭐⭐
- *"Best app for mutual funds and stocks. UI is top notch."* - ⭐⭐⭐⭐⭐
- *"They say 0 AMC but I still got charged when selling. Very confusing pricing model. Support took 2 days to reply."* - ⭐⭐

---

## 🔗 Source List

1. **Groww Pricing \u0026 Charges:** https://groww.in/pricing
2. **What are DP charges?:** https://groww.in/help/stocks/brokerage-and-charges/what-are-dp-charges
3. **Groww Account Maintenance Charges (AMC):** https://groww.in/help/stocks/brokerage-and-charges/what-are-the-account-opening-and-maintenance-charges-on-groww
4. **CDSL/NSDL Explainer:** https://groww.in/blog/what-is-nsdl-cdsl
5. **Groww Mutual Fund Charges:** https://groww.in/help/mutual-funds/brokerage-and-charges

---

## 🛡️ Where MCP Approval Happens

The **Model Context Protocol (MCP)** approval process happens directly within the **Insights Dashboard** under the **"Generated Outputs"** section. 

Once the LangGraph pipeline finishes analyzing the reviews and drafting the Product Pulse, it pauses and presents the proposed Google Docs append and Gmail draft to the user in the UI. The user can review the content, edit if necessary, and must explicitly click the **"Approve \u0026 Send via MCP"** button to execute the write actions to external tools.
