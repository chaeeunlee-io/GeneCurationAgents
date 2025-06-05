## Gene–Disease Validity Curation Demo

This repository contains a working prototype of an _LLM‑powered multi‑agent pipeline_ that automates large parts of the [ClinGen gene–disease validity curation workflow](https://clinicalgenome.org/site/assets/files/9851/gene-disease_validity_standard_operating_procedures-_version_11_docx.pdf) gene–disease validity curation workflow.

<!-- ![](gene_disease_curation/assets/pipeline.png)

![](gene_disease_curation/assets/sum_matrix.png) -->

<!-- Pipeline overview -->
<img src="gene_disease_curation/assets/pipeline.png" alt="Pipeline overview" width="200"/>

<!-- Summary matrix -->
<img src="gene_disease_curation/assets/sum_matrix.png" alt="Summary matrix" width="400"/>

Our system

1.  **Search PubMed** for a _gene × disease_ query.
2.  **Fetch abstracts** for the top _N_ papers.
3.  **Dispatch four specialist agents** (Variant, Functional, Cohort, Segregation) that independently extract structured evidence from each abstract.
4.  **Aggregate & weight** the evidence to compute per‑category scores and a provisional clinical‑validity classification ("Limited", "Moderate", "Strong", etc.).

---

### Why LLM multi‑agents for gene curation

| Manual curation | How the agents help |
| --- | --- |
| Dozens of papers must be read and scored by hand | Agents run focussed extraction passes in parallel |
| Evidence types are heterogeneous (variants vs. family segregation vs. functional assays) | Domain‑specific prompts + Pydantic parsers keep the JSON schemas disjoint yet composable |

---

### Manual effort saved

A trained curator typically needs hours to bring a single gene–disease pair to “classification‑ready”:

*   literature triage
*   per‑patient variant assessment
*   segregation analysis
*   cross‑checking public databases

---

### Code / component map

| Path | Responsibility |
| --- | --- |
| `pubmed.py` | Async PubMed search & abstract fetch |
| `agents.py` etc. | Four specialist extractor classes (prompt + parser + `analyze`) |
| `orchestrator.py` | Fan‑out / gather helper that runs the specialists per PMID |
| `/graph` | Builds the StateGraph (`search → fetch → extract → score → classify`) |
| `run_curation.py` | CLI entry‑point – `python run_curation.py BRCA1 "breast cancer"` |

---

### Extending the demo

1.  **Router node** – let an LLM decide which evidence agents to run per abstract.
2.  **Enrichment nodes** – call ClinVar & gnomAD to annotate extracted variants before scoring.
3.  **Critic loop** – add a validator agent that asks a second LLM to sanity‑check each JSON payload.
4.  **Handle reasoning traces** – log intermediate reasoning steps from each agent for traceability and feedback
5.  **Vector memory** – for better case coverage

---

### Quick‑start

```
python run_curation.py SCN1A "Dravet syndrome" --simple-ner
```

```
## Output

...
Extracting evidence from PMID 33937968
Extracting evidence from PMID 35013317
Extracting evidence from PMID 37290534
Extracting evidence from PMID 37819378
Extracting evidence from PMID 38229878
Extracting evidence from PMID 37006128

============================================================
Gene-Disease Analysis: SCN1A - Dravet syndrome
============================================================

Abstracts Analyzed: 30
Evidence Items Found: 50
Publication Years: 1993 - 2024

Evidence Scores:
  Variant: 6.76
  Functional: 5.95
  Segregation: 1.07
  Cohort: 4.71
  TOTAL: 19.87

Classification: strong
Confidence: 69.00%

Processing Time: 34.19s
```