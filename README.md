# Collaborative Software Development - Student Discount

This local project implements the Exercise 2 checkout feature. Eligible
students receive a 10% discount; non-students pay the original amount.

## Run

```powershell
python -m unittest -v
python checkout.py
```

Expected demonstration output: `90.00`.

## Git/GitHub exercise status

- [x] Project files created locally.
- [x] `add-discount` branch created locally.
- [x] Student discount implemented and tested.
- [ ] Commit: requires the user's explicit approval before creating a commit.
- [ ] Push and Pull Request: requires a real GitHub repository URL and credentials.

Suggested PR title: `Add student discount to checkout`

Suggested PR description:

> This pull request introduces a 10% discount for eligible student customers
> during checkout. It adds the discount calculation, preserves the original
> price for non-students, and includes tests for both paths and money rounding.

## Assessment answers

1. `git clone` copies a remote repository, including its history, to a local environment so it can be inspected and changed safely.
2. A repository is the complete project and its version history; a branch is an independent line of development inside that repository.
3. `git switch -c add-discount` creates a branch named `add-discount` and switches the working tree to it.
4. `git add` puts selected working-tree changes into the staging area for the next commit.
5. `git commit` records a versioned snapshot of staged changes with an explanatory message.
6. `git push` sends local commits to a remote repository; `git pull` fetches remote changes and integrates them locally.
7. A Pull Request is a request to review and merge changes from one branch into another, usually with discussion and automated checks.
8. Code review finds defects, checks standards and tests, spreads knowledge, and reduces the risk of merging problems.
9. Git may report a merge conflict when both developers changed overlapping lines; the team must resolve and test it before completing the merge.
10. Branches let developers work in parallel, isolate features, review changes, and merge only tested work into the shared main branch.
