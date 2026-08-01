# Personal Secretary Core Meta OS Requirements

| ID | Requirement | Evidence |
| --- | --- | --- |
| SEC-AUT-001 | Require current Safety-referenced grants with explicit operation, category, item, horizon, and sensitivity limits. | Authorization tests |
| SEC-BRF-001 | Produce bounded daily briefings from explicit tasks, schedule, reminders, and context. | Briefing tests |
| SEC-REV-001 | Produce deterministic weekly and monthly reviews with fixed periods and source metrics. | Review tests |
| SEC-REM-001 | Return due and upcoming reminder views without scheduling or delivery. | Reminder tests |
| SEC-REC-001 | Return advisory recommendations with rationale and evidence IDs. | Recommendation tests |
| SEC-PRI-001 | Rank tasks deterministically with transparent score reasons. | Priority tests |
| SEC-DEC-001 | Rank caller-scored options and expose trade-offs without choosing or executing. | Decision-support tests |
| SEC-AST-001 | Produce bounded personal-assistance steps with confirmation markers. | Assistance tests |
| SEC-CTX-001 | Match only approved caller-supplied context with provenance. | Context tests |
| SEC-SCH-001 | Detect conflicts and propose open time without booking. | Scheduling tests |
| SEC-PRV-001 | Reject unapproved sensitive context and retain no personal store. | Privacy/adversarial tests |
| SEC-SCP-001 | Prior Core Meta OSs, excluded domains, UI/UX, Streamlit, and deployment remain unchanged. | Frozen-scope tests |
