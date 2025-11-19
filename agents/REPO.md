# Instructions on working with the project github repo

GitHub account/repo: https://github.com/devintev/indomonitor

If github repo is set then you MUST follow these rules:
- **uphold the practice three branches**: a main branch, a dev branch and feature branches with each a PR merging back from feature branch to dev branch or a pull request to merge from dev branch to main branch.
- **Always read GitHub issues via GitHub MCP tools** when user asks about next steps or project status.
- **Use `git add .` instead of `git add filename`** unless user instructs otherwise in order to avoid missing files in the commit.
- **BEFORE creating any PR: Always run `git rebase origin/[base_branch]`** to sync feature branch with latest dev and prevent merge conflicts.
- **BEFORE pushing: Always run linters or relevant build commands** to catch errors locally before commiting.
