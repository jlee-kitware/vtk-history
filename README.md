# vtk-review-agent

A code review agent for VTK, built from VTK's own review history: merge request discussions, issues, and commit messages from gitlab.kitware.com.

The agent reads a local mirror of that history. It never queries the GitLab API directly.

## Plan

1. **Mirror.** Sync public MR and issue history into a git repository, one JSON file per item. (`mirror/`)
2. **Review examples.** For each line-level review comment, pair the comment with the code hunk it was attached to, and record whether the author changed that code in the next revision.
3. **Rules.** Cluster the examples into recurring review conventions and curate them into `REVIEW_RULES.md`, with links to the source comments.
4. **Index.** Retrieve past reviews by file path, module, VTK APIs touched, and embedding similarity.
5. **Agent.** For each hunk of a new MR, retrieve similar past reviews and applicable rules, and produce findings that each cite a rule or a past review. Findings without a citation are dropped.
6. **Evaluation.** Index only MRs merged before a cutoff date. Run the agent on the first submitted version of later MRs and compare its findings to what human reviewers said (precision, recall, findings per MR).
7. **Deployment.** Shadow mode first (private reports), then on request, then by default.

## Mirror

Use a `read_api` token from a gitlab.kitware.com account with no project or group memberships. That account sees only public content, so confidential issues and internal notes cannot enter the mirror. The script refuses a token whose account is a project member.

```bash
pip install -r requirements.txt
export GITLAB_TOKEN=...
python mirror/gitlab_mirror.py count
python mirror/gitlab_mirror.py sync --limit 200     # trial run, sync point not saved
python mirror/gitlab_mirror.py sync                 # full history, then incremental
```

The mirror is written to `data/vtk-history/`, which is its own git repository (one commit per sync) and is excluded from this repository. Re-running `sync` fetches only items updated since the last sync and refetches each changed item's full history.
