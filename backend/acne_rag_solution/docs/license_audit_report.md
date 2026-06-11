# Evidence License Audit Report

Generated: 2026-06-06 (Asia/Seoul)

## Scope
This audit covers the local RAG evidence corpus used by the skin-lesion guidance MVP. It records every evidence card and every distinct source URL used by `evidence_corpus.json`.

## Reuse Policy
- Generation-allowed evidence: `public_domain`, `cc0`, `cc_by`, `commercial_allowed`.
- Excluded from generated grounding by default: `citation_only`, including NC/ND-like, unclear, copyrighted, or dataset-license-pending sources.
- Stored text is project-authored Korean paraphrase/summary, not copied source passages. Source links are retained for attribution and verification.
- Images, figures, tables, logos, and dataset files are not reused in the RAG corpus unless separately cleared.

## Corpus Summary
- Total evidence cards: 143
- `cc_by`: 83
- `public_domain`: 51
- `citation_only`: 9
- Unique source URLs: 33
- Duplicate evidence IDs: 0

## License Verification Anchors
- NIAMS text: official disclaimer says website text is public domain; images require separate clearance. Verification: https://www.niams.nih.gov/About_Us/Contact_Us/disclaimer.asp
- CDC text: Use of Agency Materials says most CDC/ATSDR website information is public domain, with attribution/no-endorsement requirements. Verification: https://www.cdc.gov/other/agencymaterials.html
- NCI text: reuse policy says NCI text is free of copyright unless otherwise indicated, with credit requested. Verification: https://www.cancer.gov/policies/copyright-reuse
- PMC articles: generation-allowed PMC additions were checked through Europe PMC REST metadata with `license=cc by`; CC BY-NC items stay citation-only.

## Class Coverage
| class | total cards | generation allowed | distinct generation sources | distinct generation URLs |
|---|---:|---:|---:|---:|
| `blackhead` | 13 | 12 | 5 | 3 |
| `whitehead` | 13 | 12 | 5 | 3 |
| `papule` | 16 | 15 | 7 | 4 |
| `pustule` | 16 | 15 | 7 | 4 |
| `cystnnodule` | 11 | 10 | 6 | 3 |
| `complexacne` | 11 | 10 | 2 | 3 |
| `milia` | 11 | 9 | 1 | 2 |
| `rosacea` | 12 | 11 | 2 | 3 |
| `seborrheic` | 12 | 11 | 2 | 2 |
| `sebdermatitis` | 15 | 14 | 2 | 2 |
| `atopic` | 14 | 13 | 4 | 4 |
| `psoriasis` | 14 | 13 | 4 | 4 |
| `normal` | 8 | 7 | 2 | 2 |
| `abnormal` | 10 | 9 | 2 | 3 |

## Files Produced
- `docs/evidence_cards_register.csv`: one row per evidence card.
- `docs/evidence_sources_register.csv`: one row per distinct source URL, including verification method and generation/citation decision.

## Remaining Publication Risks
- Dataset image licenses are separate from RAG text evidence. Kaggle, Roboflow, AIHub, and DermNet dataset terms must be cited and checked independently in the dataset section of the KCC paper.
- Some classes still rely heavily on one authoritative source family, but each low-diversity class now has at least one official/public-domain or CC BY source and source-register traceability.
- Before camera-ready submission, rerun this audit and re-check URLs marked `citation_only` if the paper text cites them beyond simple references.

