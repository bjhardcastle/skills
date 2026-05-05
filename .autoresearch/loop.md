carry on executing the steps below forever, user will stop when ready:

- execute `benchmark.md`
- commit changes to `SKILL.md` and push to the repo
- regenerate performance plot from the updated `performance.tsv` 
- commit all and push to the repo
- the first run is the baseline. for subsequent runs, compare the results to the previous:
    - if the mean score improved by 0.1 or more, keep the changes and go to the next iteration
    - if the score declined or did not improve significantly, revert to the previous commit and try new modifications
- in a subagent named "modifier" (`gpt-5.5` max effort):
    - work for no more than 2 minutes
    - change one major aspect of [SKILL.md](skills/personal/apply-allen-brand/SKILL.md) to more-effectively communicate the Allen Institute brand guidelines for visualizations with AI agents.
    - some ideas: 
        - simplify / cut down on content
        - add more specifics
        - add more examples
    -  `benchmark.md` will be used to evaluate effectiveness of the updated skill
    - only modify `SKILL.md` - do not modify any other files
