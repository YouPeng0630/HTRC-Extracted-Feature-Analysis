# HTRC Extracted Features Analysis for PHUG
This repo contains data and code for our DCMI 2026 paper:
**Equitable Metadata for Diverse Voices: Sustainable Computational Poetry Analysis with HathiTrust Extracted Features**
We map the PHUG poetry dataset to HTRC Extracted Features (EF v2.5) and test whether EF can still support computational poetry research after HTRC infrastructure retirement.

## Data Description
**PHUG (Poets from Historically Underrepresented Groups)** is a curated collection of American poetry in the HathiTrust Digital Library (HTDL) by poets from historically underrepresented groups. It includes poem-level boundary annotations (start/end pages) so we can align poems with page-based EF records.
In this repo, `data/Boundary Data/` holds the boundary files organized by group (AA, APA-AA, APA-PA, LXA, NA).  
`data/HTRC Extract Feature Download/` stores the EF volume files we used (compressed JSON, `.json.bz2`).  
`data/Wordcloud/` contains the word cloud images produced for each group.
**Coverage:** with EF v2.5, we matched **all 120 volumes and 4,723 poems (100%)**.
## Code
- `src/HTRC_EF_download_rsync_2.5.ipynb` — download / sync EF files for the PHUG volumes (rsync workflow).
- `src/poem_extraction.py` — extract poem-level tokens from EF using PHUG boundaries and prepare inputs for analysis.
- `src/wordcloud.ipynb` — build group-level word clouds from the extracted vocabulary.

**Data availability.** The PHUG-derived HTRC Extracted Features dataset is archived on Zenodo  
([record](https://zenodo.org/records/19261037); DOI: [10.5281/zenodo.19261037](https://doi.org/10.5281/zenodo.19261037)).

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
