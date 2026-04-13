# HTRC Extracted Features Analysis for PHUG
This repo contains data and code for our DCMI 2026 paper:
**Equitable Metadata for Diverse Voices: Sustainable Computational Poetry Analysis with HathiTrust Extracted Features**
We map the PHUG poetry dataset to HTRC Extracted Features (EF v2.5) and test whether EF can still support computational poetry research after HTRC infrastructure retirement.


## Dataset Description
### PHUG (base dataset)
- 4,724 poems
- 120 poetry collections
- Includes poem-level boundary metadata (start/end pages)
- Covers poets from historically underrepresented groups in the U.S.
### EF-mapped PHUG (this repo)
- PHUG volumes aligned to HTRC Extracted Features
- Primary version: **EF v2.5**
- Match result: **100% coverage**
- Includes token-level frequency inputs used in analysis


## Repository Structure
```text
.
├── data/
│   ├── Boundary Data/                  
│   │   ├── aa_poets/
│   │   ├── apa-aa_poets/
│   │   ├── apa-pa_poets/
│   │   ├── lxa_poets/
│   │   └── na_poets/
│   ├── HTRC Extract Feature Download/  
│   └── Wordcloud/                     
│       ├── aa_poets.png
│       ├── apa-aa.png
│       ├── apa-pa.png
│       ├── lxa_poets.png
│       └── na_poets.png
└── src/
    ├── HTRC_EF_download_rsync_2.5.ipynb
    ├── poem_extraction.py
    └── wordcloud.ipynb
