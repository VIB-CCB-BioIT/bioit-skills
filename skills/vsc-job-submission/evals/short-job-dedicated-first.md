---
query: which partition should I use for a 2 hour alignment job?
should_trigger: true
notes: Partition choice for a short job. Without the skill the model picks the default public partition (batch_graniterapids, or worse a wICE batch queue) and bills credits for work that runs free on dedicated_big_bigmem — the dedicated-first ordering and the sam-balance access check exist nowhere else.
---
