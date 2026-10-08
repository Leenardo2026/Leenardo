# Leenardo — Agent Rules (mandatory in every conversation)
- Do not run git push, git pull, or git fetch. Network git is done by the user via GitHub Desktop. When a branch or main is ready to push, stop and tell the user exactly which branch to push.
- Never merge to main or trigger a deploy unless the user explicitly says so in a separate message. Every push to main costs Netlify credits.
- Always work on a separate branch; record every new branch in BRANCHES.md.
- On macOS the sandbox blocks writes to .git/. BypassSandbox is allowed ONLY for local git write commands: git add, git commit, git rm, git switch/checkout -b, local git merge. Before each bypass, state the exact command in chat. NEVER bypass for git push/pull/fetch, deletions, network access, package installs, or any other command. If such a command is blocked: STOP and report the exact command and why it was needed.
- Ask before any destructive or irreversible action, even if the command is not blocked.
- Never print, store, or embed tokens, keys, or passwords in commands or files.
- Code, comments, and file names in English; user-facing text is multilingual.
- Diagnose before fixing: for unclear bugs, report the root cause with evidence first, then wait.
- Do not simply agree. Before acting on an instruction or confirming a claim (from the user or from Claude), verify it against the code or official docs. If something is wrong, risky, or there is a simpler/safer way to reach the same goal, say so BEFORE acting and propose the alternative. Then wait for a decision.
- After editing any HTML or JS file, syntax-check every changed inline <script> block and JS file with node before committing. Never commit code that fails to parse.
- Syntax checks do not catch undefined names. For every identifier you add or reference in a change, verify it is declared and in scope (file:line) before committing.

## Lessons 2026-10-05
- Never use a command, mode, flag or file the task does not explicitly allow. If something seems necessary, stop and ask.
- Answer every requested report section; write MISSING for anything not done. Never report success for checks not implemented.
- The sandbox blocks network; "not allowed by policy" errors come from the sandbox, not from servers. Do not diagnose them as server/RLS problems.
- Never open, read or print .env. Never run upload scripts with --confirm.
- Repo SQL files may differ from the live database; never assume live state from migration files.
- every grep -r must use --exclude='.env*'
- answer every requested section
- READ ONLY tasks: no node -e or other scripts, use only allowed commands
- a claim that a behavior is broken must be marked UNVERIFIED unless tested live
