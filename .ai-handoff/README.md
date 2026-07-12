# ChatGPT and Antigravity Handoff Workspace

This directory is the controlled handoff workspace between the project owner, ChatGPT, and Antigravity.

## Roles & Responsibilities

* **Project Owner**: Defines project goals, manages access credentials, verifies visual outputs, and moves approved/completed task folders to the archive.
* **ChatGPT**: Acts as Product Architect, reviews requirements, code modifications, test evidence, and provides the final approval gate for all changes.
* **Antigravity**: Implementation engineer. Executes code changes, runs test suites, compiles verification evidence packages, and prepares pull requests.

---

## Directory Workflow

The workflow utilizes the following subdirectories:

1. **`01_CHATGPT_TO_ANTIGRAVITY/`**: Intake folders containing tasks assigned by ChatGPT or the Project Owner.
2. **`02_ANTIGRAVITY_WORK/`**: Work packages, test logs, code diff patches, and rollback plans prepared by Antigravity.
3. **`03_CHATGPT_REVIEW/`**: Review notes, feedback, or verification remarks compiled by ChatGPT.
4. **`04_APPROVED_FOR_PUSH/`**: Formal record of authorized push approvals.
5. **`05_REJECTED_OR_REVISION/`**: Details of rejected work packages or revision instructions.
6. **`99_ARCHIVE/`**: Completed task folders moved by the Project Owner.

---

## Strict Approval Authority Rules

### 1. Verification Authority
Antigravity must **never** originate, infer, or self-create a ChatGPT approval. An approval file is valid only when:
* ChatGPT explicitly provides the completed approval text.
* The Project Owner places that exact text into the approval folder, or explicitly instructs Antigravity to copy it there.
* The approval contains the matching task ID.
* The approval contains the exact phrase: `APPROVED FOR PUSH`.

### 2. Forbidden Inferences
Antigravity may **not** create an approval file based on:
* A positive or complimentary review comment.
* A statement that a plan is "safe" or "good to go".
* A recommendation or instruction to continue.
* An implementation prompt.
* Antigravity's own test results or interpretations.

---

## Push & Merge Authority Separation

Antigravity operates under two distinct, explicit gates:

### Gate A: APPROVED FOR PUSH
This gate is unlocked only when a matching approval file containing the phrase `APPROVED FOR PUSH` and the task ID is present in `04_APPROVED_FOR_PUSH/`.
* **Permitted Actions**: Committing approved work locally, pushing the approved branch to remote, and opening or updating a draft pull request.
* **Prohibited Actions**: Merging the pull request.

### Gate B: APPROVED TO MERGE
This gate is unlocked only when the Project Owner or ChatGPT explicitly states `APPROVED TO MERGE` in the conversation.
* **Permitted Actions**: Merging the reviewed pull request.
* **Prohibited Actions**: Merging based on a push approval or implicit assumptions.

---

## Shared Handoff Architecture
* **GitHub as the Visibility Layer**: GitHub is the shared source of truth for visibility and review.
* **Local Directories**: The local Windows directory is a convenience workspace for active execution, not the source of truth for the workflow.
* **Code Base**: The production Git repository is the absolute source of truth for application code. Handoff documents must remain isolated under the `.ai-handoff/` folder.
