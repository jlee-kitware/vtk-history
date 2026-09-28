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

The mirror stores every public discussion thread on VTK merge requests and issues, including line-level review comments and the diff positions they are attached to. It gets code from git, not the API: `--repo` fetches every merge request head into a local VTK clone, and diffs are reconstructed from the `base_sha` and `head_sha` recorded on each review comment. That leaves one API request per item.

GitLab does not serve discussions anonymously, so a token is required. Use a `read_api` token from a gitlab.kitware.com account with no project or group memberships (create it in a private browser window). That account sees only public content, so confidential issues and internal notes cannot enter the mirror. The script refuses a token whose account is a project member.

```bash
pip install -r requirements.txt
export GITLAB_TOKEN=...
python mirror/gitlab_mirror.py count
python mirror/gitlab_mirror.py sync --limit 200                   # trial run, sync point not saved
python mirror/gitlab_mirror.py sync --repo /home/jlee/gitsync/vtk # full history, then incremental
```

The first full sync is about 20,000 requests at one per second (5 to 6 hours). Tell the GitLab administrators the window beforehand and run it overnight. The script backs off on HTTP 429 and 5xx responses, and an interrupted sync resumes where it stopped. Later syncs fetch only items updated since the previous one.

The mirror is written to `data/vtk-history/`, which is its own git repository (one commit per completed sync) and is excluded from this repository.
