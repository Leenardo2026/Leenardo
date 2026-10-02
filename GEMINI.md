# Leenardo — Agent Rules (mandatory in every conversation)
- Do not run git push, git pull, or git fetch. Network git is done by the user via GitHub Desktop. When a branch or main is ready to push, stop and tell the user exactly which branch to push.
- Never merge to main or trigger a deploy unless the user explicitly says so in a separate message. Every push to main costs Netlify credits.
- Always work on a separate branch; record every new branch in BRANCHES.md.
- If any command is blocked by permission settings, STOP and report: (1) the exact command, (2) why it was needed. Do NOT try workarounds (e.g. find -delete instead of rm).
- Ask before any destructive or irreversible action, even if the command is not blocked.
- Never print, store, or embed tokens, keys, or passwords in commands or files.
- Code, comments, and file names in English; user-facing text is multilingual.
- Diagnose before fixing: for unclear bugs, report the root cause with evidence first, then wait.
