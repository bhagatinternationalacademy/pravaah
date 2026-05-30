# 🌊 PRAVAAH ERP Suite

PRAVAAH is a next-generation Institutional ERP and Workflow Management Portal designed to coordinate course pipeline stages, facilitate instant Gate 0 feasibility checklists, enforce granular Role-Based Access Control (RBAC), and automate trainer billing ledger cycles.

---

## 🚀 Key Modules & Capabilities

### 🛡️ 1. Security & RBAC Gateway (`usermgmt`)
* **Secure Authentication**: Handles user registration, email verification cycles, token lifecycles, and brute-force protections centrally.
* **Role-Based Access Control**: Standard users are directed away from sensitive interfaces. Permissions are validated dynamically using an advanced Role-Permission Matrix.
* **Central Audit Trail**: Chronologically logs every structural database change, login attempt, and authentication event.

### 📋 2. Course Proposals & Marketing Pipeline (`proposalmgmt`)
* **Pipeline Registration**: Record, search, and manage upcoming courses, dates, and hosting institutes.
* **Gate 0 Feasibility Check**: Validates essential physical constraints (training rooms, hostel capacities, trainer availability, and financial feasibility) before routing.
* **Detailed Gate Approval Data Entry**: Prompts operators to register deep structural checklist parameters across all 9 operational segments (Session plans, Technical checklists, Assessment plans, Invoicing schedules, etc.).
* **Marketing Review Board**: A dedicated queue for the Marketing team to review, add feedback, and authorize or reject pending proposals.

### 💸 3. Billing & Disbursals Ledger (`billingmgmt`)
* **Trainer Workspace**: Allows trainers to upload invoice documents (PDFs) and monitor ledger milestones.
* **Accounts Audit**: A custom portal for accounts staff to audit line-item expenses, approve invoices, or reject them with feedback.
* **Disbursal Clearance**: A final gateway allowing the Trainer Admin to authorize payments, log disbursal records, and trigger automated in-app notifications.

---

## 👥 Personas & Testing Accounts

To facilitate comprehensive, end-to-end testing across all workflow roles, the database has been populated with standard testing accounts (Password: `Guru@om459`):

| Role | Username | Email | Permissions / Scope |
| :--- | :--- | :--- | :--- |
| **Superuser & Marketing** | `harshada2576` | `harshada2576@gmail.com` | Unlimited access, bypasses RBAC, manages Marketing Review Queue. |
| **Standard Marketing Reviewer** | `marketing1` | `marketing1@pravaah.edu` | Accesses the Marketing Queue to approve or return gate proposals. |
| **Accounts Auditor** | `accounts1` | `accounts1@pravaah.edu` | Accesses the Accounts Ledger to approve or reject trainer bills. |
| **Trainer Administrator** | `traineradmin1` | `traineradmin1@pravaah.edu` | Performs final disbursal authorization and logs cleared bills. |
| **Trainer** | `trainer1` | `trainer1@pravaah.edu` | Uploads invoices and tracks personal billing milestones. |

---

## 📊 Pre-Populated Testing Cases (Real-Life Scenarios)

The system automatically initializes realistic testing scenarios to demonstrate full pipeline dynamics:

### A. Course Pipeline Scenarios
1. **Raw Proposal**: *Advanced Machine Learning & Neural Networks* at *IIT Bombay*. A newly created proposal waiting for its Gate 0 feasibility check.
2. **Gate 0 Failed**: *Cybersecurity Incident Response Bootcamp* at *COEP*. Fails feasibility checks (marked 'No' for hostel availability and financial feasibility).
3. **Passed Gate 0**: *Cloud Architecture & DevOps Masterclass* at *VJTI Mumbai*. Passed Gate 0 (all 'Yes'), waiting for detailed Gate Approval data entry.
4. **Awaiting Marketing Review**: *Full-Stack Software Engineering Accelerator* at *BMS College*. Gate Approval submitted with realistic checkpoints, currently sitting in the Marketing Queue.
5. **Returned / Rejected**: *Blockchain & Smart Contracts Specialization* at *RV College*. Rejected by Marketing due to missing session plans; alerts show marketing feedback.
6. **Fully Approved**: *Artificial Intelligence & Big Data Analytics* at *IIT Madras*. Approved by Marketing and fully authorized.

### B. Billing Ledger Scenarios
1. **Submitted**: Invoice `INV/2026/001` (45,000 INR) uploaded by Trainer, waiting for Accounts audit.
2. **Under Accounts Review**: Invoice `INV/2026/002` (12,450 INR) uploaded by Trainer, currently being audited.
3. **Approved by Accounts**: Invoice `INV/2026/003` (35,000 INR) successfully audited, waiting for Trainer Admin disbursal.
4. **Rejected by Accounts**: Invoice `INV/2026/004` (8,200 INR) returned with feedback requesting valid receipts.
5. **Under Trainer Admin Review**: Invoice `INV/2026/005` (60,000 INR) undergoing final clearance reviews.
6. **Payment Cleared**: Invoice `INV/2026/006` (120,000 INR) approved and disbursed.
7. **Rejected by Trainer Admin**: Invoice `INV/2026/007` (95,000 INR) returned due to deviation from pre-approved hourly consulting rates.

---

## 🛠️ Installation & Setup

1. **Clone & Environment Setup**:
   ```bash
   git clone <repository_url>
   cd pravaah
   ```

2. **Database Schema Integration**:
   *Ensure MySQL is active with database `pravaah` configured in your `settings.py`.*
   *(Do NOT run schema mutations/migrations unless structure changes occur; the schema is pre-synced).*

3. **Start Development Server**:
   ```bash
   python manage.py runserver
   ```
   *The server binds to `http://127.0.0.1:8000/`.*

4. **Populate/Reset Test Scenarios**:
   ```bash
   python manage.py shell -c "exec(open('create_dummy_data.py').read())"
   ```
