# MonkeyZoo Studio — Repository Governance & Workflow

This document outlines the branching, review, and merging workflow for the MonkeyZoo Studio repository.

## Development Workflow

1. **Create Feature Branch**: branch off of `main` using a descriptive name (e.g. `feat/my-feature` or `fix/some-bug`).
2. **Develop**: implement code changes and verify functionality.
3. **Run Tests**: execute the automated test suite locally:
   ```bash
   pytest
   ```
4. **Push**: push the feature branch to origin.
5. **Open Draft PR**: open a Draft Pull Request on GitHub targeting the `main` branch.
6. **ChatGPT Review**: wait for review from ChatGPT. The Project Owner will coordinates the review loop.
7. **Revise if Needed**: implement any requested feedback and push updates.
8. **APPROVED TO MERGE**: once ChatGPT provides final approval, the Project Owner will authorize the merge. Only the exact phrase `APPROVED TO MERGE` permits merging.
9. **Merge**: merge the pull request using **Squash Merge** only.
10. **Delete Branch**: clean up the remote feature branch.

---

## Handoff Workspace Scope (High-Risk Only)
The `.ai-handoff/` evidence package and push-approval files are **only** required for high-risk work:
* Backend architecture changes
* Canon or continuity modifications
* Production pipeline rewrites
* Release automation
* Destructive migrations
* Security-sensitive changes
* Large multi-module changes

For ordinary frontend, documentation, styling, bug fixes, and small feature work, the draft pull request is the complete review package and does not require push-approval records.
