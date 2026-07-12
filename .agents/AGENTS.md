# MonkeyZoo Comic Factory — Project Rules

## 1. ChatGPT & Antigravity Handoff Protocol

All task coordination, review packages, and approval records must be kept completely isolated from the application code under the `.ai-handoff/` directory.

### Strict Approval Authority Rules
* **No Inferred Approvals**: Antigravity must never originate, infer, or self-create a ChatGPT approval file.
* **Approval Validity**: An approval file is valid only when:
  1. ChatGPT explicitly provides completed approval text.
  2. The Project Owner places that exact text into the approval folder (`.ai-handoff/04_APPROVED_FOR_PUSH/`) or explicitly instructs Antigravity to copy it there.
  3. The approval contains the matching Task ID.
  4. The approval includes the exact phrase: `APPROVED FOR PUSH`.
* **Prohibited Inferences**: Antigravity must not assume or create approval records based on positive reviews, statements that a plan is safe/ready, instructions to continue, or its own test results.

### Separate Push and Merge Gates
Antigravity must treat push and merge authorities as two distinct, non-implied gates:
1. **APPROVED FOR PUSH**: Permits committing approved work, pushing the branch, and updating draft pull requests. *Does not permit merging.*
2. **APPROVED TO MERGE**: Triggered only by the explicit phrase `APPROVED TO MERGE` in the conversation. Permits merging the pull request.

---

## 2. Frontend & Static Pages Truthfulness Audits

### Dynamic Status Indicators
* Do not hardcode "Active" or "Online" server indicators in UI layouts.
* Status panels must default to a checking state (e.g. `Checking backend status...`) and dynamically probe the backend endpoint.
* In static demo modes (such as GitHub Pages), the status must clearly display `Local backend required` or similar, indicating that a local server is needed.

### Mock-Data Truthfulness
* All simulated or mock records (cast traits, story scripts, history logs, issue titles) must be explicitly and visibly tagged with `[Demo Placeholder]`.
* Real issue data parsed from the repository metadata must be tagged with `[Repository Metadata]`.
* Under static mode, state-altering API writes must be blocked, alert the user with a warning about local backend requirements, and return explicit failure payloads.

---

## 3. Deployment & Build Safety

### Sync Idempotency
* Any script designed to synchronize static files (e.g., `sync_docs.ps1`) must be idempotent.
* Successive runs of the sync script must produce exactly zero changed bytes or file differences.
