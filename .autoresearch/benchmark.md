- in a subagent named "generator" (`gpt-5.5` max effort):
    - read [SKILL.md](skills/personal/apply-allen-brand/SKILL.md) 
    - add Allen branding to `base_plot.py` and save it as `mod_plot.py` - DO NOT modify `base_plot.py` directly
    - run `uv run --script .autoresearch/mod_plot.py` to generate the new plot with Allen Institute visual style
- in a subagent named "evaluator" (`gpt-5.5` max effort):
    - evaluate `plot.png` against the `Brand Cheat Sheet.pdf` (its content is already extracted out into `cheatsheet.md`, but you can also look at the pdf for visuals)
    - rate each of the following out of 5 based on Allen Institute brand guidelines and general visual design principles:
        1. Effective color palette (we assume it used colors from the Allen palette, but did it use them in a visually appealing way?)
        2. Typography adherence
        3. Layout and composition
    - add a row to `performance.tsv` (create the file if it doesn't exist)
