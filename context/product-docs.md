# FlowDesk — Product Documentation

## Getting Started

### Creating Your Account
1. Go to flowdesk.io → click "Start for free"
2. Sign up with Google or email
3. Verify your email (check spam if not received within 2 min)
4. Complete the 4-step onboarding wizard (takes ~5 minutes)

### Inviting Team Members
- Go to **Settings → Team → Invite Members**
- Enter email addresses (comma-separated for bulk invite)
- Free plan: max 3 members including yourself
- Members receive an invite email valid for 7 days; resend from Settings → Team

---

## Projects & Boards

### Creating a Project
1. Click **"+ New Project"** on the sidebar
2. Choose a template or start blank
3. Set visibility: Private (only invited members) or Team (all workspace members)

### Views
- **Board (Kanban):** Drag cards between columns
- **List:** Spreadsheet-like view, sortable by any field
- **Timeline (Gantt):** Pro+ only — shows tasks on a date range
- **Calendar:** Tasks with due dates shown on a monthly calendar

### Task Fields
Every task has: Title, Assignee, Due Date, Priority (P1–P4), Status, Labels, Attachments, Comments.
Custom fields (text, number, dropdown, date) available on Starter+.

---

## Automations

### How Automations Work
Automations = "When [trigger] → Do [action]"

**Common triggers:** Task created, status changes, due date approaches, assignee changes, form submitted

**Common actions:** Assign task, send Slack notification, move to project, set due date, create subtask, send email

### Automation Limits
- Free: 0 automations
- Starter: 50 runs/month
- Pro: Unlimited runs
- Enterprise: Unlimited + custom triggers via webhooks

### Troubleshooting Automations
- Automation not firing? Check: Is it enabled (toggle in Automations panel)? Does the trigger match exactly?
- Hit the limit? Upgrade plan or wait for the monthly reset (1st of each month)
- Automation running twice? Check for duplicate automation rules

---

## Integrations

### Slack Integration
1. Settings → Integrations → Slack → "Connect"
2. Authorise the FlowDesk Slack app
3. Choose which projects send notifications to which channels
4. To disconnect: Settings → Integrations → Slack → "Disconnect"

### Gmail Integration
1. Settings → Integrations → Gmail → "Connect"
2. Sign in with Google; approve permissions
3. Forward support emails or link to tasks automatically
4. Note: This is for forwarding only, not two-way sync

### Jira Integration (Pro+)
1. Settings → Integrations → Jira → enter your Jira subdomain + API token
2. Map FlowDesk projects to Jira projects
3. **Known issue:** First sync may create duplicate tasks — delete duplicates and re-sync
4. Two-way sync updates within 5 minutes of changes on either side

### Zapier
- Find "FlowDesk" in Zapier's app directory
- Use your API key from Settings → Developer → API Keys
- Supports 40+ triggers and actions

---

## Billing & Subscriptions

### Changing Your Plan
- Go to **Settings → Billing → Change Plan**
- Upgrades take effect immediately (prorated charge)
- Downgrades take effect at next billing cycle

### Payment Methods
- Credit/debit cards (Visa, Mastercard, Amex)
- ACH bank transfer (Enterprise only)
- All billing via Stripe

### Invoices
- Found in Settings → Billing → Invoice History
- Sent automatically to billing email on each charge

### Cancellation
- Settings → Billing → Cancel Subscription
- You retain access until end of current billing period
- Data retained for 90 days after cancellation; export before then
- No refunds on monthly plans; annual plans: prorated refund if cancelled within 30 days

### Free Trial
- New accounts get 14-day Pro trial automatically
- No credit card required for trial
- After trial, reverts to Free plan unless upgraded

---

## Account & Security

### Password Reset
1. Go to flowdesk.io/login → "Forgot password"
2. Enter your email → receive reset link (valid 1 hour)
3. If no email received: check spam, or contact support

### SSO (Enterprise)
- Supports SAML 2.0 and Google Workspace SSO
- Setup: Settings → Security → SSO Configuration
- Requires: Entity ID, SSO URL, Certificate from your IdP
- Test SSO before enforcing (use "Test" button before "Enforce SSO")

### Two-Factor Authentication (2FA)
- Settings → Security → Two-Factor Auth
- Supports authenticator apps (Google Authenticator, Authy) and SMS
- Backup codes generated on setup — save them!

### Data & Privacy
- Data stored in AWS us-east-1 (US) by default
- EU data residency available on Enterprise (AWS eu-west-1)
- SOC 2 Type II certified (report available on request)
- GDPR compliant; DPA available on request

---

## Mobile App

### Available On
- iOS 15+ (App Store)
- Android 10+ (Google Play)

### Known Mobile Limitations (as of v2.3)
- Timeline (Gantt) view not available on mobile
- Automations can be viewed but not created on mobile
- Offline mode: read-only for last synced data

### Notifications
- Push notifications enabled via app permissions
- Configure per-project in app: tap Project → Settings → Notifications

---

## Common Error Messages

| Error | Meaning | Fix |
|-------|---------|-----|
| "Workspace limit reached" | Hit user/project limit for plan | Upgrade or remove unused members |
| "Automation limit exceeded" | Hit monthly automation run cap | Upgrade plan or wait for monthly reset |
| "Integration auth expired" | OAuth token expired | Reconnect integration in Settings |
| "Sync conflict detected" | Two users edited same field simultaneously | Accept one version; other is in revision history |
| "File too large" | Attachment exceeds plan limit | Free: 10MB/file; Starter: 50MB; Pro: 250MB |
| "Session expired" | Logged out after inactivity | Log back in (sessions expire after 30 days) |
