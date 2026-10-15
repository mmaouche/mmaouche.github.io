# Academic website

Static website hosted on GitHub Pages.

## Local preview

```sh
python3 -m http.server 8000
```

Open http://localhost:8000.

## Publications

The page retains a saved publication list and queries HAL on each visit.
A GitHub Actions workflow refreshes the bundled arXiv feed daily.
Publications are merged, deduplicated, and sorted newest first.
Paper links prefer HAL, then arXiv, then DOI.
If a source is unavailable, saved publications remain visible.

Refresh the arXiv feed locally with:

```sh
python3 scripts/update_arxiv.py
```

The workflow is in `.github/workflows/update-arxiv.yml` and can also be run
manually from the repository's Actions tab. It requires repository contents
write permission. On the published site, the arXiv feed is read from the
repository, with the bundled copy as fallback.

## Themes

The header toggle switches between light and dark mode. The preference is saved
in browser storage; otherwise the site follows the system preference.

## Publishing changes

After changing CSS or JavaScript, update the asset versions before committing:

```sh
python3 scripts/version_assets.py
python3 scripts/version_assets.py --check
```

Publish the updated HTML alongside the assets so browsers load matching versions.

## Local LaTeX export

Generate and compile a CV from the website:

```sh
python3 scripts/build_cv.py
```

The output is written under `build/cv/`. The layout is defined in
`templates/academic-cv.tex`. Compilation requires Tectonic, XeLaTeX, or LuaLaTeX.
Tectonic downloads and caches its packages on the first run.

Use `--offline` to use saved publication data, or `--tex-only` to generate LaTeX
without compiling. Keep the generated `assets/` folder alongside the LaTeX source
when compiling elsewhere.

Local tool installations, generated output, and local document storage are
excluded from Git by `.gitignore`.

## Converter checks

```sh
python3 -m unittest discover -s tests -v
```
