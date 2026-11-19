# Glossary: lie-detection probes

Project terms for the notebook's writing rules (principle 22). To move into the project's own repo when the `record` skill is written.

- **Readout:** how a probe's per-token scores become one score for a response. The three are last-token, mean-pool and max-pool.
- **Set and split:** "set" means a dataset (instructed lies, harm-pressure v2, sandbagging); "split" is used only for train, dev and test.
- **Dataset names** are written exactly as here: instructed lies, harm-pressure v2, convincing-game, sandbagging.
- **Skyline:** a probe trained on the target set, as the best score reachable there.
- **Arms:** the conditions an experiment compares, such as the three training sets in a training-set comparison.
- Every comparison uses "vs".
