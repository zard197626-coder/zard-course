# Collaborative Software Development - Student Discount

This repository contains the Git and GitHub collaborative software development
exercise. Eligible students receive a 10% discount during checkout; non-students
pay the original amount.

## Feature

- Students pay 90% of the original total.
- Non-students pay the original total.
- Money is calculated with `Decimal` and rounded to two decimal places.

## Run

```powershell
python -m unittest -v
python checkout.py
```

Expected demonstration output for a £100 student purchase: `90.00`.

## Branches

- `main`: integrated project code.
- `add-discount`: feature branch used for the exercise Pull Request.

## Exercise status

- [x] Project files created locally.
- [x] `add-discount` branch created.
- [x] Student discount implemented and tested.
- [x] Changes committed and pushed to GitHub.
- [x] Pull Request created.
- [x] Feature merged into `main`.

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
