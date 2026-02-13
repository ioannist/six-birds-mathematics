# Results dashboard

## Build status
- Lean: (not checked by script)
- Pytest: (not checked by script)

## Exhibit A: Calculus closure

### Finite difference Leibniz identity (Python)
- python/sbt_math/diffops.py

### Stencil flow (stability only)
- generated_total: 1000, survivors_total: 913
- survivors_by_best_fit_k: {'0': 913, '1': 0, '2': 0}
- output_path: data/runs/stencil_flow_20260127_212335.json

### Stencil flow (Leibniz-gated)
- survivors_total: 50
- survivors_by_best_fit_k: {'1': 50}
- figure: figures/stencil_flow_leibniz_last_run.svg
- figure_png: figures/stencil_flow_leibniz_last_run.png

### Integration closure
- output_path: data/runs/integration_closure_20260213_174738.json
- figure_svg: figures/integration_closure_last_run.svg
- figure_png: figures/integration_closure_last_run.png
- rm exponent: 1.0000909928978714, rm r2: 0.9999999977757404
- ft(trap) exponent: 0.4999545087666289, ft(trap) r2: 0.9999999977756714

### False-positive hunt
- false_positive_total: 0
- passed_leibniz_total: 6

## Exhibit A: Protocol holonomy
- fit_p: 1.4638055029257755
- output_path: data/runs/holonomy_rm_20260127_212336.json
- figure: figures/holonomy_rm_last_run.svg
- figure_png: figures/holonomy_rm_last_run.png

## Exhibit B: Prime closure diagnostics
- figure: figures/prime_closure_rm_last_run.svg
- figure_png: figures/prime_closure_rm_last_run.png
- trend_summary: conv rm2 decreases: 4; strip rm2 decreases: 0

conv_table:
| N | rm2 | errS2 | errP2 |
| --- | --- | --- | --- |
| 50 | 0.07597451 | 0.2090832 | 0.14698719 |
| 100 | 0.06978029 | 0.171755 | 0.11187126 |
| 200 | 0.06673144 | 0.14231887 | 0.08481302 |
| 400 | 0.06130345 | 0.1184859 | 0.0654121 |
| 800 | 0.05239908 | 0.09848514 | 0.05056767 |

strip_table:
| N | rm2 | errS2 | errP2 |
| --- | --- | --- | --- |
| 50 | 340.42084518 | 6.59171449 | 2123.74765548 |
| 100 | 5996.53581334 | 10.43290278 | 60260.82731892 |
| 200 | 619843.10286871 | 16.5012263 | 9848850.07827024 |
| 400 | 314453912.4689081 | 27.12017358 | 8291350147.845939 |
| 800 | 5008084385726.176 | 43.70767414 | 216626703791640.4 |

## Exhibit B: Passivity toy
- figure: figures/passivity_toy_last_run.svg
- figure_png: figures/passivity_toy_last_run.png
| lambda | mean_dev | max_dev |
| --- | --- | --- |
| 1.0 | 0.87169354 | 7.10508878 |
| 0.7 | 0.58006786 | 4.26785665 |
| 0.4 | 0.34952484 | 2.26657293 |
| 0.2 | 0.20051341 | 1.21606142 |
| 0.1 | 0.09468919 | 0.71825583 |
| 0.0 | 0.00030292 | 0.00090919 |

## Framework index
- total labels: 108
- env counts: corollary: 5, definition: 25, equation: 10, lemma: 16, other: 29, remark: 14, theorem: 9
- notes/framework_index_summary.md

## Reproduction commands
- python experiments/stencil_flow/run.py
- python experiments/stencil_flow/leibniz_gate.py
- python experiments/stencil_flow/hunt_false_positives.py
- python experiments/holonomy_rm/run.py
- python experiments/integration_closure/run.py
- python experiments/prime_closure_rm/run.py
- python experiments/passivity_toy/run.py
