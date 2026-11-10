# Working style: keep token use low

I'm on a Claude Pro plan with limited usage, so work economically.

- Read only what the task needs. Search for the relevant function or lines
  before opening a whole file, and don't re-read files you've already seen
  in this conversation.
- Make targeted edits instead of rewriting whole files.
- Don't start subagents, workflows, or web searches unless I ask for them.
- For anything larger than a small fix, tell me the plan in a few lines and
  wait for my OK before you start.
- When running code, keep the output short: run the smallest test that
  proves the change works, and trim long output.
- If a fix fails twice, stop and tell me what you found instead of
  continuing to try things.
- Keep replies short: what you changed, whether it worked, and anything I
  need to decide. No long recaps or unrequested extras.
- Do only what I asked. Mention other problems you notice in one line each
  rather than fixing them.
