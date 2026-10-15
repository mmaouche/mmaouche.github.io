# Mohamed Maouche — personal website

Static website hosted on GitHub Pages. To preview locally:

```sh
python3 -m http.server 8000
```

Open http://localhost:8000.

## Publications

`index.html` contains the saved publication list, available without JavaScript or network access.
`assets/js/publications.js` queries HAL’s public API on every page load, with a ten-second timeout.
It updates links for matching papers and merges newly found papers with the saved list.
The combined list is sorted by publication year, newest first, then by title within each year.
The first four papers are visible; the rest appear under “More publications & preprints”.
The saved HTML is also sorted, so the ordering works without a live HAL response.
Papers are deduplicated by HAL ID, version-independent arXiv ID, DOI, and normalized title.
Identity aliases are retained when sources use different titles. HAL links and publication years
win over arXiv metadata. Data is inserted as text, never HTML.
Only records with the exact author name Mohamed Maouche are included; HAL types are ART, COMM, or UNDEFINED.
An author HAL identifier would further disambiguate this query if namesakes appear in the future.

### arXiv-only papers

arXiv does not allow cross-origin browser requests. `.github/workflows/update-arxiv.yml`
fetches arXiv daily at 05:23 UTC (GitHub may delay scheduled runs), on changes to the updater,
or manually through Actions → Update arXiv publications → Run workflow.
The standard-library-only `scripts/update_arxiv.py` saves `assets/data/arxiv.json`.
The initial snapshot is included so local preview works immediately.

The workflow runs on `master`, requires GitHub Actions and repository contents write permission,
and commits refreshed data there. After merging these changes into `master`, the workflow becomes active.
The public `mmaouche.github.io` site reads the JSON from `raw.githubusercontent.com` on each visit,
with the bundled snapshot as fallback. This avoids relying on a Pages rebuild after bot commits.
Local previews read the bundled JSON. To refresh locally:

```sh
python3 scripts/update_arxiv.py
```

HAL still refreshes live on each visit. arXiv updates daily, rather than querying arXiv on each visit.
Each source loads independently; failure of either source does not prevent the other from displaying papers.
The publication status displays the arXiv snapshot date.

Link preference: HAL → arXiv → publisher DOI. Browser updates do not modify `index.html`.
Periodically update the saved list for offline readers. Google Scholar is not scraped.

## Student supervision sources

The Students section includes publicly documented co-supervision, rather than inferring supervision from coauthorship.
Checked 15 October 2026:

- Alix Ntoutoume Nzame: [Vincent Roca’s supervision page](https://www.inrialpes.fr/planete/people/roca/roca_supervision.html), [Privatics 2023 report](https://radar.inria.fr/report/2023/privatics/index.html), and [CITI directory](https://www.citi-lab.fr/smart-people/): CIFRE with OpenSezam since December 2023, co-supervised by Mohamed Maouche, Vincent Roca and Pierre-Guillaume Gourio-Jewell.
- Imen Bajar: [her public account of the brain MRI project](https://fr.linkedin.com/in/imen-bajar/fr) explicitly thanks Mohamed Maouche and Carole Frindel as supervisors; the [Privatics 2025 report](https://radar.inria.fr/report/2025/privatics/index.html) lists her as a PhD student since November 2025. Mohamed Maouche also confirmed Héber Hwang Arcolezi and Antoine Boutet as co-supervisors on 15 October 2026.
- Yacine Belal: [LIRIS 2025 report](https://liris.cnrs.fr/sites/default/files/Documents/faits_marquants/LIRIS-FAITS-MARQUANTS-2025.pdf) identifies Mohamed Maouche as co-supervisor and Sonia Ben Mokhtar as supervisor; [his CV](https://yacinebelal.github.io/files/YacineBelal_CV.pdf) gives January 2022–June 2025 and a June 10, 2025 defense.

- Julien Nicolas: co-supervision confirmed directly by Mohamed Maouche on 15 October 2026. The [LIRIS thesis record](https://liris.cnrs.fr/these/these-julien-nicolas) provides the topic and November 2023 start; the supplied CV documents the joint INSA Lyon–McGill PhD, and [Mila](https://mila.quebec/fr/annuaire/julien-nicolas) identifies Mark Coates as supervisor at McGill.
- Ousmane Touat: co-supervision confirmed directly by Mohamed Maouche on 15 October 2026. The [LIRIS thesis record](https://liris.cnrs.fr/these/these-ousmane-touat) provides the topic, 2024 start, and Sonia Ben Mokhtar’s supervision.

Other internships cannot be reconstructed reliably from the available public sources.

Julien Nicolas and Ousmane Touat are grouped under “PhD co-supervision outside Privatics”, with their LIRIS / DRIM affiliation, following Mohamed Maouche’s clarification.

## Software from publications

The existing Anonymization Metrics, HMC, and SFERA entries remain in Research tools.
Additional software is listed in a second category within the same Software section, crediting the paper’s first author as Contributor
at Mohamed Maouche’s request. This label does not claim sole authorship or repository maintainership.
Repository links were taken from the papers or the original project, checked 15 October 2026:

- Brain MRI privacy evaluation — Imen Bajar. [Paper’s reproducibility statement](https://arxiv.org/html/2610.20494v1) links `mri-reid-privacy-86C3` on anonymous.4open.science.
- Giskard — Ousmane Touat. [Paper, open-science appendix](https://arxiv.org/html/2606.19129v1) links `Giskard-ByzRobustConfidentialDL-B3E9`.
- GRANITE — Yacine Belal. [Paper, evaluation environment](https://arxiv.org/html/2504.17471v1) links `Granite-Byzantine-Resilient-Dynamic-Gossip-Learning-Framework-4886`.
- Decentralized learning privacy evaluation — Ousmane Touat. [Paper’s contributions](https://arxiv.org/html/2412.12837v1) link `ExposingVulneDL`.
- ACCIO — Vincent Primault. [Original repository](https://github.com/privamov/accio) redirects to `pvcnt/accio`; it is archived. [Paper record](https://discovery.ucl.ac.uk/id/eprint/10047858/) confirms the first author and publication association.

Anonymous repositories are labelled as such. Their URLs are documented by the papers;
several could not be inspected through the research browser, so ongoing availability is not guaranteed.
No repository is invented for publications where a corresponding code release was not found.

### Incoming PhD student

Sami Kouzeiha was added to Privatics supervision following Mohamed Maouche’s direct confirmation.
Start year: 2026, marked Incoming. Topic: “Evaluating and Enforcing Privacy in Agentic AI”.
The supplied project proposal, `On_the_Security_and_Privacy_of_Agentic_AI.pdf` (January 2026),
provides the research axes and identifies Sonia Ben Mokhtar, Raouf Kerkouche and Mohamed Maouche
as the scientific team. The student's identity and team placement come from the user, not the proposal.
The proposal itself is not copied to the public site.

### Student profile links

Student names link to personal websites where identified; otherwise LinkedIn:

- Ousmane Touat: https://otouat.github.io/ (linked as his personal page by LIRIS; the research browser could not retrieve the site directly).
- Yacine Belal: https://yacinebelal.github.io/ (verified personal research page).
- Julien Nicolas: https://www.linkedin.com/in/j-nicolas/ (McGill / INSA Lyon joint PhD in privacy-preserving decentralized learning; distinguished from namesakes).
- Imen Bajar: https://www.linkedin.com/in/imen-bajar/ (Inria / Polytech Lyon).
- Alix Ntoutoume Nzame: https://www.linkedin.com/in/alix-ntoutoume/ (OpenSezam).
- Sami Kouzeiha: https://www.linkedin.com/in/sami-kouzeiha-6a29a2220/ (Télécom Paris / machine learning).

No personal websites were found for the four LinkedIn entries during this search.

## Project participation

Projects describe participation and roles, independently of student supervision.
Roles confirmed directly by Mohamed Maouche: INESIA co-PI with Sonia Ben Mokhtar and Raouf Kerkouche;
RAIDAC+ member; REDEEM non-funded member; IPoP (PEPR Cybersécurité) member;
OpenSezam CIFRE PI with Vincent Roca; Riviera PI with Carole Frindel.
Project context for IPoP: https://www.pepr-cybersecurite.fr/projet/ipop/.
Existing dates for REDEEM described PhD supervision rather than the full project, so they were removed.
No personal participation dates were inferred for IPoP.

Student project affiliations confirmed by Mohamed Maouche: Julien Nicolas and Ousmane Touat are part of REDEEM; Imen Bajar is part of MIAI. These affiliations are linked in their student entries.

Imen Bajar’s PhD is a cotutelle with ÉTS Montréal, confirmed directly by Mohamed Maouche.

Additional academic service confirmed directly by Mohamed Maouche: SRDS 2019 local organizing committee; ANR AAPG 2023 (CE23) reviewer; organization of the FIL 10th anniversary and FIL federated learning workshop. No dates were inferred for the two FIL events.

## News

The 2026 news entries cover INESIA funding (confirmed by Mohamed Maouche and the supplied CV/project proposal) and Yacine Belal’s GDR RSD thesis award, verified against the [official award announcement](https://gdr-rsd.cnrs.fr/laureats-du-prix-de-these-du-gdr-2026/). Dates are shown by year, consistent with the rest of the site.

Header research profiles: ORCID `0000-0001-6473-7173` verified through DBLP (`223/6875`); HAL profile `mohamed-maouche`. The arXiv link uses an author search rather than an unverified author identifier.

The ESI education logo comes from the [official ESI logos page](https://www.esi.dz/logos/), using its [color logo](https://www.esi.dz/wp-content/uploads/2019/12/logo_esi-600x249.png).

## Local LaTeX CV

Generate a typeset academic CV from the website and compile it locally:

```sh
python3 scripts/build_cv.py
```

Outputs:

- `build/cv/Mohamed-Maouche-CV.pdf`
- `build/cv/Mohamed-Maouche-CV.tex` (editable generated source)
- `build/cv/Mohamed-Maouche-CV.build.log` (compiler output)

The content comes from `index.html`, including closed disclosures. The converter
also merges the bundled arXiv feed and queries HAL, with the same HAL → arXiv → DOI
link preference and duplicate detection as the website. If HAL is unavailable,
saved publications are retained. Past research experience and education appear
in separate sections. The website's news, menus, and disclosure controls are omitted.

Edit `templates/academic-cv.tex` to change the layout: TeX Gyre Pagella type,
slate blue and green accents, section icons, aligned dates, numbered references,
and page numbers. The header includes the existing portrait, and institution logos
appear beside experience, education, and teaching entries. Update
website content in `index.html`, then regenerate; direct edits to the generated
`.tex` will be overwritten on the next run. No browser or Python packages are needed.

Each generated CV folder includes an `assets/` directory containing its portrait,
institution logos, and the existing Font Awesome icon font (SIL OFL 1.1).
Keep that directory alongside the `.tex` file when compiling elsewhere or uploading
to Overleaf. The `.past-experience` spans in `index.html` identify the two previous
appointments without changing their presentation on the website. The ENTPE logo
is taken from the [official institutional website](https://www.entpe.fr/sites/default/files/logo_entpe_site_web.png).

The script finds **Tectonic**, **XeLaTeX**, or **LuaLaTeX** on PATH, or a local
`.tools/tectonic` binary. Tectonic is installed locally in this working copy;
`.tools/` and `build/cv/` are ignored by Git. To set up another machine, install
[Tectonic from its official instructions](https://tectonic-typesetting.github.io/en-US/install.html)
or use an existing XeLaTeX/LuaLaTeX installation. Tectonic caches its packages and fonts
under `.tools/cache/`; its first compilation needs internet access.

Useful options:

```sh
# Use saved publication data (compilation is fully offline once TeX files are cached).
python3 scripts/build_cv.py --offline

# Only generate the source, for editing or importing into Overleaf.
python3 scripts/build_cv.py --offline --tex-only

# Use a specific compiler or a separate output directory.
python3 scripts/build_cv.py --engine /path/to/tectonic --output-dir /tmp/my-cv

# Reproduce a build using a downloaded HAL API response.
python3 scripts/build_cv.py --offline --hal-json /path/to/hal-response.json
```

This is a local authoring tool. There is no public CV-generation button or server
endpoint. The website publication refresh continues to work independently.

Converter checks: `python3 -m unittest discover -s tests -v`.

## Website theme

The header’s **Dark mode** button switches between the original gray and green light
palette and the deep forest dark palette. Blue remains a separate color for
hyperlinks in both modes. `assets/js/theme.js` applies the saved
`maouche-theme` browser preference before rendering; without a saved choice, it
follows the system theme. The button supports keyboard use, and switching still
works when browser storage is blocked. The local LaTeX CV is independent of this setting.

## Updating browser assets before publishing

After editing CSS or JavaScript, run:

```sh
python3 scripts/version_assets.py
```

This stamps local stylesheet and script URLs in `index.html` with their content hashes.
Commit the updated HTML together with the changed assets so returning visitors receive
matching files instead of an older cached stylesheet. Verify with
`python3 scripts/version_assets.py --check`.
