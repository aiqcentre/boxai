# Ways of Working

## Branch Strategy
- **Main branch is locked** – no direct commits.
- All changes must be made through **Pull Requests (PRs)**.
- Use **one branch per contributor per active feature**.
  - Branch name format: `feature/<short-description>` (e.g., `feature/user-login`).

## Workflow
1. **Create a branch** from `main` for your assigned feature.
2. Commit and push changes to your branch regularly.
3. Open a **Pull Request** to `main` when ready for review.
4. At least **one approval** is required before merging.
5. Keep your branch updated with `main` via rebase or merge.

## Reviews & Merges
- No self-approval for PRs.
- Squash merge is preferred for a clean history.
- Delete branches after merge.
