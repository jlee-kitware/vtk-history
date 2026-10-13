# vtk-review-agent

A code review agent for VTK, built from VTK's own review history: merge request discussions, issues, and commit messages from gitlab.kitware.com.

The agent reads a local mirror of that history. It never queries the GitLab API directly.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env    # then edit: VTK clone, Ollama server, tokens
```

`config.py` reads `.env` and the environment. By default it expects a VTK clone at `../vtk`, beside this repository,
with the `upstream` remote (https://gitlab.kitware.com/vtk/vtk.git) fetched, and an Ollama server on
`http://localhost:11434`. The data the tools build goes in `data/`, which git ignores.

## Plan

1. **Mirror.** Sync public MR and issue discussions into a git repository, one JSON file per item. (`mirror/`, done)
2. **Review examples.** For each review thread, recover the code the reviewer saw from the local VTK clone and record whether the author changed it afterward. (`extract/`, done)
3. **Rules.** Cluster the examples into recurring review conventions and curate them into `REVIEW_RULES.md`, with links to the source comments.
4. **Design dossiers.** One summary per module or major class: its purpose, the key decisions and the MRs where they were made, approaches tried and reverted, known pitfalls, and deprecations. Built from git history, MR discussions, and issues, and updated as new MRs merge.
5. **Index.** Retrieve past reviews by file path, module, VTK APIs touched, and embedding similarity.
6. **Agent.** An agent loop that investigates each change with tools before writing findings (see below). Every finding cites a rule, a past review, or a commit; findings without a citation are dropped.
7. **Evaluation.** Index only MRs merged before a cutoff date. Run the agent on the first submitted version of later MRs and compare its findings to what human reviewers said (precision, recall, findings per MR).
8. **Deployment.** Shadow mode first (private reports), then on request, then by default. Rejected findings feed back into the rules and dossiers.

## Agent tools

The agent chooses which of these to use for each change:

- `search_reviews`: past review threads on similar code, by path, module, API, and text
- `file_history`: `git log`, `git blame`, and the MRs behind a file or line range
- `design_dossier`: the dossier for a module or class
- `review_rules`: the curated conventions that apply to the change
- `search_issues`: related bug reports, including fixes that were reverted
- `read_code`: surrounding source, callers, and tests at the MR's revision

## Data sources

Added in this order; each goes through the same mirror, extract, label, and index steps.

1. GitLab merge requests and issues (`mirror/gitlab_mirror.py`). Issues include the Mantis reports migrated in 2016 (titles and report text).
2. VTK Discourse (`mirror/discourse_mirror.py`): about 7,800 public topics, one file per topic, about 8,000 requests. Posts are CC BY-NC-SA 3.0, recorded on each file.
3. Mantis discussions (2003 to 2016), from the frozen HTML export at `vtk.org/Bug/view.php?id=N`; the IDs come from the migrated GitLab issues.
4. The vtkusers and vtk-developers mailing lists, if the Mailman archives can be obtained.

## Review examples

```bash
python extract/extract_reviews.py --mirror data/vtk-history --repo $VTK_REPO
```

Writes `data/review_examples.jsonl`, one review thread per line, tagged `line` (with the diff hunk and surrounding source at the reviewed revision), `legacy` (pre-2016 line comments whose positions GitLab no longer has), `general`, or `approval`. Merge robot and CI bot messages, robot command lines, and mention-only comments are removed. Revisions missing from the clone are fetched from `upstream` by hash.

## Mirror

The mirror stores every public discussion thread on VTK merge requests and issues, including line-level review comments and the diff positions they are attached to. It gets code from git, not the API: `--repo` fetches every merge request head into a local VTK clone, and diffs are reconstructed from the `base_sha` and `head_sha` recorded on each review comment. That leaves one API request per item.

GitLab does not serve discussions anonymously, so a token is required. Use a `read_api` token from a gitlab.kitware.com account with no project or group memberships (create it in a private browser window). That account sees only public content, so confidential issues and internal notes cannot enter the mirror. The script refuses a token whose account is a project member.

```bash
pip install -r requirements.txt
export GITLAB_TOKEN=...
python mirror/gitlab_mirror.py count
python mirror/gitlab_mirror.py sync --limit 200                   # trial run, sync point not saved
python mirror/gitlab_mirror.py sync --repo $VTK_REPO # full history, then incremental
```

The first full sync is about 20,000 requests at one per second (5 to 6 hours). Tell the GitLab administrators the window beforehand and run it overnight. The script backs off on HTTP 429 and 5xx responses, and an interrupted sync resumes where it stopped. Later syncs fetch only items updated since the previous one.

The mirror is written to `data/vtk-history/`, which is its own git repository (one commit per completed sync) and is excluded from this repository.
