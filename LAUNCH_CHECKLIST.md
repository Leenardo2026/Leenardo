# Launch Checklist (must be done before public launch)

- [ ] Enable email confirmation in Supabase Auth (currently OFF — anyone can sign up with someone else's email)
- [ ] Spanish gloss audit: find "correct POS, wrong word family" errors (e.g. "yaşar" → "vidas") — result pending
- [ ] Decide Supabase plan: free tier + heartbeat vs Pro ($25/mo) once the live site depends on Supabase for articles
- [ ] Verify Supabase Auth redirect URLs point to leenardo.com (not localhost / old previews)
- [ ] Re-check RLS on all tables (saved_words, articles): no "anyone can write" rules left
- [ ] Rename legacy `mia_` localStorage keys to `leenardo_` (with migration so users don't lose data)

# Housekeeping
- [ ] ~8 Oct 2026: delete `feature/media-and-homepage-optimization` if the live site has been stable
