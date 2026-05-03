---
name: work-afk
description: "Use when the user says work-afk, asks to work AFK issues, ready-for-agent issues, or queued issues while away. Runs the user's AFK loop: lowest issue number first, one subagent per task using the best current model at maximum available reasoning effort, commit each completed issue with the issue number in the commit title, push, then continue."
---

# Work AFK

Run this loop:

> Work on AFK issues in order from lowest to highest. Use subagents with the best current model at maximum available reasoning effort for each task. Commit each when done with a reference to the issue number in the commit message title, then push and move onto the next.
