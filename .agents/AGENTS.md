# MonkeyZoo Comic Factory — Project Rules

## 1. ChatGPT & Antigravity Handoff Protocols

Tasks are categorized into **Normal Tasks** and **High-Risk Tasks**.

### A. Normal Task Workflow
Used for ordinary frontend, documentation, styling, bug fixes, and small feature work. The draft pull request is the complete review package.
1. Create a dedicated feature branch.
2. Make only the requested changes.
3. Run the required tests and verify changes.
4. Commit the work locally.
5. Push the branch to remote origin.
6. Open a draft pull request.
7. Report:
   * Pull Request URL
   * List of changed files
   * Test results
   * Known limitations or caveats
8. Stop and wait for review. **Do not merge automatically.**
* **Note**: No separate push-approval files or `.ai-handoff/` directories are required for normal tasks.

### B. High-Risk Task Workflow
Required **only** for high-risk work:
* Backend architecture changes
* Canon or continuity modifications
* Production pipeline rewrites
* Release automation
* Destructive migrations
* Security-sensitive changes
* Large multi-module changes

For these tasks, the full package under `.ai-handoff/` must be compiled, and the formal push/merge gates must be followed.

---

## 2. Push & Merge Gates (For High-Risk Work)

When high-risk workflow gates are active, Antigravity operates under two distinct, explicit approvals:

### Gate A: APPROVED FOR PUSH
* **Requirement**: A matching approval file containing the phrase `APPROVED FOR PUSH` and the task ID must be present in `.ai-handoff/04_APPROVED_FOR_PUSH/`.
* **Verification**: Antigravity is strictly forbidden from self-creating, inferring, or originating approval files. It must be explicitly provided as completed approval text by ChatGPT and placed by the Project Owner.
* **Permitted Actions**: Committing approved work locally, pushing the approved branch to remote, and opening or updating a draft pull request.
* **Prohibited Actions**: Merging the pull request.

### Gate B: APPROVED TO MERGE
* **Requirement**: A matching approval file containing the phrase `APPROVED TO MERGE` and the task ID must be present in `.ai-handoff/06_APPROVED_TO_MERGE/`.
* **Permitted Actions**: Merging the reviewed pull request.
* **Prohibited Actions**: Merging based on a push approval, a positive review, or implicit assumptions.
* **Expiration**: A merge approval becomes invalid if the pull request head commit changes after the approval is written.

---

## 3. Frontend & Static Pages Truthfulness Audits

### Dynamic Status Indicators
* Do not hardcode "Active" or "Online" server indicators in UI layouts.
* Status panels must default to a checking state (e.g. `Checking backend status...`) and dynamically probe the backend endpoint.
* In static demo modes (such as GitHub Pages), the status must clearly display `Local backend required` or similar, indicating that a local server is needed.

### Mock-Data Truthfulness
* All simulated or mock records (cast traits, story scripts, history logs, issue titles) must be explicitly and visibly tagged with `[Demo Placeholder]`.
* Real issue data parsed from the repository metadata must be tagged with `[Repository Metadata]`.
* Under static mode, state-altering API writes must be blocked, alert the user with a warning about local backend requirements, and return explicit failure payloads.

---

## 4. Deployment & Build Safety

### Sync Idempotency
* Any script designed to synchronize static files (e.g., `sync_docs.ps1`) must be idempotent.
* Successive runs of the sync script must produce exactly zero changed bytes or file differences.
