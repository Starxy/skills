# Review RED — Figure/Table Selection Contract

## Contract

The approved design requires the final explanation to select one or two Figure/Table items that are necessary for the core mechanism or main evidence. Compact citations may still use section, theorem, algorithm, figure, or table anchors, but the response must not separately explain more than two Figure/Table items.

## Preserved failing outputs

| Artifact | Selected or separately explained Figure/Table items | Result |
|---|---|---|
| `green-algorithm.md` | Table 1 complexity, Table 2 translation results, Table 3 ablation, Table 4 parsing, plus appendix attention figures | FAIL |
| `variation-theory-rerun.md` | Figure 1 logistic/IMDB, Figure 2 MNIST/SFO, Figure 3 CIFAR-10, Figure 4 VAE bias-correction ablation | FAIL |

## Passing comparison outputs

| Artifact | Selected or separately explained Figure/Table items | Result |
|---|---|---|
| `green-perspective.md` | Table 1 scale trend | PASS |
| `variation-title-only-rerun.md` | Table 2 ImageNet controlled comparison and Table 6 CIFAR-10 depth boundary | PASS |

## Root cause

`SKILL.md` says “至多选取两个”, but does not make the selection observable or distinguish a compact source anchor from a separately explained item. As a result, outputs can summarize a sequence of three or more figures/tables while still appearing to satisfy the wording. This is a RED behavioral failure discovered by final independent review; the original raw outputs remain unchanged.
