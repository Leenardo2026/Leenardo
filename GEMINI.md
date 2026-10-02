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
