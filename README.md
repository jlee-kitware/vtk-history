# vtk-history

Tools that make VTK's development history usable for maintenance work, and the evaluations that measure how well each one works.

VTK's history holds knowledge maintainers need: why code is written the way it is, what was tried before, who knows each part, and what reviewers expect. It is spread across 11 years of GitLab merge requests (MRs) and review discussions, 8 years of Discourse threads, and 32 years of commits. This project mirrors that history locally, indexes it, and builds tools on it. Each tool is tested by replaying past MRs with only the history that existed before each one, and comparing against what actually happened.

This work is part of an NIH-funded effort on VTK maintenance.

## What it provides

| Tool | What it does | Measured |
| --- | --- | --- |
| Related history | Finds earlier issues, MRs and forum threads related to an MR from its title and description | The issue an MR fixes is in the top 5 of about 3,700 issues for 84% of MRs (300 tested) |
| Reviewer suggestions | Ranks people by recent reviews and commits on the files an MR changes, with their usual response time | An actual reviewer is in the top 3 for 76% of MRs (1,656 tested), against 67% for the most active reviewers |
| MR briefing | Gathers related history, suggested reviewers, conventions reviewers applied to the changed files, deprecated APIs in the added code, and recent commits on those files | About 4 seconds per MR |
| Review conventions | 217 conventions distilled from 1,490 review comments, each with an estimate of how often authors act on it | Brier score 0.194 against 0.218 for the base rate, on held-out comments |
| Clang-tidy candidates | Conventions that an existing clang-tidy check could enforce | 25 conventions, behind 15% of convention comments, match checks VTK does not enable |
| Deprecations | Every API VTK deprecated: when, why, in which MR, and whether it was removed | |
| Area label suggestions | Suggests an `area:` label for issues that have none, from the most similar labeled issues and MRs, the files changed by MRs that link the issue, and the issue template's Language and Graphics backend lines. Labels that name a technology (`area:wasm`, `area:webgpu`, `area:qt`, ...) need the issue to name it. Below a confidence cutoff (0.7) the issue is marked "no label fits" | Above the cutoff, right for 95% of 315 labeled issues tested one at a time, and 91% of 54 issues filed since 2024 using only labels from before; always suggesting `area:build` is right for 42% |
| GitLab labels | Search filtered by label, labels shown on search results and in the briefing | |
| Module group labels | Proposes one label per top-level VTK directory (`area:common`, `area:filters`, ... reusing `area:rendering`, `area:io` and the other existing labels), read from the files an MR changes; for an issue, from its linked MRs or the VTK classes it names | 10,314 of 13,759 MRs and 3,313 of 5,193 issues would get one; on 598 issues with both, the named classes agreed with the linked MRs' files 73% of the time |
| Trends | Terms, code areas, themes and GitLab `area:` and `lang:` labels whose share of MRs, issues or forum topics rose or fell | |
| Search | Keyword and meaning search over MRs, issues, review threads, forum posts, blog posts, docs and release notes | |
| Commit index | 79,907 commits on master since 1994, with the functions each changed and, for 25,667 of them, the MR that merged it | |

The app (`app/`) presents all of these in a browser.

## What did not work

These results are negative and are kept because they are measured.

- An AI review agent (a local model, and gpt-5.4-mini through OpenAI) raised the same concern as a VTK reviewer for about 1 comment in 25. Adding mined conventions, tool results, or compiler and clang-tidy output did not change that. For scale, two VTK reviewers on the same MR comment within 5 lines of each other only 10 to 17% of the time.
- Ranking conventions by file history did not predict which one a reviewer would raise (19% in the top 10, against 20% for the 10 most common).
- Given a reviewer's comment, gpt-5.4-mini wrote an acceptable fix for 53% of 150 comments. Examples drawn from the history (similar comments, random earlier fixes, or earlier commits to the same function) did not improve it; differences stayed within the model's run-to-run variation.

The code for these is in `agent/` and `eval/`.

## Setup

Requirements: Python 3.10 or newer, git, a VTK clone, and an Ollama server for embeddings and local models.

```bash
git clone https://gitlab.kitware.com/vtk/vtk.git ../vtk      # or point VTK_REPO at an existing clone
git -C ../vtk remote add upstream https://gitlab.kitware.com/vtk/vtk.git
pip install -r requirements.txt numpy
cp .env.example .env                                         # then edit
```

`config.py` reads `.env` and the environment:

| Setting | Default | Used for |
| --- | --- | --- |
| `VTK_REPO` | `../vtk` | Code, history, and the diffs behind review comments |
| `OLLAMA_HOST` | `http://localhost:11434` | Embeddings (qwen3-embedding) and local models (qwen3-coder-next, gpt-oss:120b) |
| `GITLAB_TOKEN` | none | Mirroring GitLab discussions |
| `OPENAI_API_KEY` | none | Only the OpenAI experiments |
| `VTK_REVIEW_WORKTREE`, `VTK_REVIEW_BUILD` | `../vtk-review-wt`, `../vtk-review-build` | Only the developer-check experiment |

Everything the tools build goes in `data/`, which git ignores.

## Building the data

The steps run in this order. `refresh.sh` runs all of them after the first sync and brings the data up to date.

1. **Mirror the sources.**
   ```bash
   python mirror/gitlab_mirror.py sync --repo $VTK_REPO    # MRs, issues and all review threads
   python mirror/discourse_mirror.py sync                  # discourse.vtk.org topics
   python mirror/blog_mirror.py sync                       # Kitware blog posts about VTK
   ```
   GitLab does not serve discussions anonymously. Use a `read_api` token from a gitlab.kitware.com account with no project or group memberships, so only public content can enter the mirror; the script refuses a token whose account is a project member. The first GitLab sync is about 20,000 requests at one per second (5 to 6 hours); tell the GitLab administrators beforehand. Later syncs fetch only what changed. The mirror is its own git repository in `data/vtk-history/`.
2. **Extract review examples.** `python extract/extract_reviews.py` recovers the code each line comment was written on and records whether the author changed it before the MR merged.
3. **Label threads.** `python label/label_reviews.py` tags each thread with a topic and any convention it states, using a local model.
4. **Conventions.** `rules/draft_rules.py`, `rules/verify_rules.py` and `rules/merge_rules.py` turn labeled threads into conventions; `rules/doc_rules.py` and `rules/tool_rules.py` collect what VTK's documentation and tools already state; `rules/confidence.py` estimates follow-through.
5. **Deprecations.** `python deprecations/build_index.py`
6. **Reviewer expertise.** `python people/expertise.py build`
7. **Trends.** `python trends/discover_terms.py` and `python trends/discover_themes.py`
8. **Search index.** `python index/build_index.py` (about 104,000 documents; embedding takes a few hours on one GPU)
9. **Commit index.** `python index/commits.py build`, then `python index/commits.py embed` (about 80,000 commits, about 4 hours)
10. **Labels.** `python trends/label_trends.py` for label trends, and `python triage/area_labels.py` for area label suggestions (`data/labels/area_suggestions.csv`, one row per unlabeled issue with the suggested label or "no label fits", the best guess, its confidence, and the precision measured at that confidence; `--issue N` suggests for one issue). The search index stores GitLab labels when it is built; `python index/labels.py` adds them to an index built before that.

## Running the app

```bash
python3 -m venv --system-site-packages ~/venvs/trame4 && ~/venvs/trame4/bin/pip install "trame>=4" trame-mui numpy
bash app/run.sh        # serves http://localhost:8080
```

Tabs: Briefing, Review, Rules, Deprecations, Trends, Labels, Search. Labels shows what applying the area label suggestions would add, how accurate they were on issues maintainers already labeled, and a lookup for one issue (`#123`) or merge request (`!123`). Every control has a tooltip that says what it does.

## Reproducing the measurements

| Result | Command |
| --- | --- |
| Related issues and MRs | `python eval/related_history.py` (add `--title-only` for the title-only baseline) |
| Reviewer suggestions | `python people/expertise.py backtest --since 2025-01-01` |
| Follow-through estimates | `python rules/adjusted.py` and `python rules/estimate.py` |
| Predicting review concerns | `python eval/review_concerns.py --cutoff 2024-07-01` |
| Reviewer agreement | `python eval/reviewer_agreement.py` |
| Review agent | `python bench/build_benchmark.py`, then `python agent/evaluate.py --agent tool` and `python agent/judge_comments.py score <run directories>` |
| Area label suggestions | `python triage/area_labels.py` (report in `data/labels/AREA_LABELS.md`); `--mrs` for labeled merge requests |
| Module group labels | `python triage/module_labels.py` (report in `data/labels/MODULE_LABELS.md`) |
| Writing fixes | `python eval/fix_suggestions.py build --n 150`, `run --model <model> [--history \| --code-history]`, `score <labels>`, then `python eval/fix_stats.py` |

Runs that call OpenAI log their token use to `data/logs/openai_usage.jsonl` and stop when the logged cost reaches `OPENAI_BUDGET_USD` (default $2).

## Layout

| Directory | Contents |
| --- | --- |
| `mirror/` | GitLab, Discourse and blog mirrors |
| `extract/`, `label/` | Review examples from the mirror, and their labels |
| `rules/` | Conventions, their verification, follow-through estimates, documented and tool rules |
| `people/` | Reviewer expertise and suggestions |
| `deprecations/` | Deprecation index |
| `trends/` | Term and theme trends |
| `index/` | Search index, commit index, and GitLab labels |
| `triage/` | Area label suggestions and proposed module group labels |
| `ontology/` | VTK modules and classes, from the source tree |
| `app/` | The trame app, including the MR briefing |
| `eval/` | Evaluations of the tools |
| `agent/`, `bench/` | The review agent, its benchmark, and the judge |

## Data sources and terms

All sources are public. GitLab content comes from gitlab.kitware.com/vtk/vtk. Discourse posts from discourse.vtk.org are licensed CC BY-NC-SA 3.0, which each mirrored topic records. Kitware blog posts come from the site's public API. The mirrored text keeps its original terms; the license below covers this project's code.

## License

BSD 3-Clause. See `LICENSE`.
