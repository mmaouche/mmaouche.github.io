"""Checks for the website-to-LaTeX converter; no TeX installation is needed."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_cv', ROOT / 'scripts/build_cv.py')
cv = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = cv
spec.loader.exec_module(cv)


class CVTests(unittest.TestCase):
    def record(self, title, **fields):
        return {'title_s': [title], 'authFullName_s': ['Mohamed Maouche'],
                'publicationDateY_i': 2026, **fields}

    def test_hal_priority_and_transitive_aliases(self):
        # A bridging record joins a renamed HAL paper and its arXiv preprint.
        records = [
            self.record('New title', halId_s='hal-12345678'),
            self.record('Old title', arxivId_s='2601.12345v2', publicationDateY_i=2025),
            self.record('New title', arxivId_s='2601.12345v3'),
        ]
        papers = cv.merge_publications([], records)
        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0]['url'], 'https://hal.science/hal-12345678')
        self.assertEqual(papers[0]['year'], 2026)
        self.assertIn('title:oldtitle', papers[0]['keys'])

    def test_arxiv_precedes_doi_and_sort_is_by_year(self):
        records = [
            self.record('Older paper', halId_s='hal-12345678', publicationDateY_i=2019),
            self.record('A newer paper', doiId_s='10.1234/example'),
            self.record('A newer paper', arxivId_s='2601.12345', doiId_s='10.1234/example'),
        ]
        papers = cv.merge_publications([], records)
        self.assertEqual([p['year'] for p in papers], [2026, 2019])
        self.assertEqual(papers[0]['url'], 'https://arxiv.org/abs/2601.12345')

    def test_other_authors_are_ignored(self):
        record = self.record('Unrelated', arxivId_s='2601.12345')
        record['authFullName_s'] = ['Someone Else']
        self.assertEqual(cv.merge_publications([], [record]), [])

    def test_latex_special_characters_and_urls_are_escaped(self):
        self.assertEqual(cv.escape(r'R&D 50% #1_{x} \input{bad}'),
                         r'R\&D 50\% \#1\_\{x\} \textbackslash{}input\{bad\}')
        link = cv.href('https://example.org/?x=1&y=%C3%A9#part', 'ÉTS Montréal')
        self.assertIn(r'x=1\&y=\%C3\%A9\#part', link)
        self.assertEqual(cv.href('javascript:alert(1)', 'label'), 'label')

    def test_closed_sections_and_accented_names_are_exported(self):
        page = cv.PageParser()
        page.feed((ROOT / 'index.html').read_text())
        papers = cv.saved_publications(page.root)
        result = cv.render_cv(page.root, papers)
        source = result['CONTENT']
        self.assertEqual(result['ROLE'], 'Tenured Research Scientist at Inria')
        for expected in ['ÉTS Montréal', 'Héber Hwang Arcolezi', 'IMWUT',
                         'Dimensionality reduction', 'Computer Science Engineering degree',
                         'AP-Attack', 'Contributor:']:
            self.assertIn(expected, source)
        self.assertNotIn('View journals and years', source)
        self.assertNotIn('More publications', source)
        self.assertNotIn('fa-download', source)
        self.assertGreater(len(papers), 15)

    def test_experience_education_and_visual_assets(self):
        page = cv.PageParser()
        page.feed((ROOT / 'index.html').read_text())
        result = cv.render_cv(page.root, cv.saved_publications(page.root))
        source = result['CONTENT']
        experience_heading = r'\cvsection{F0B1}{Past research experience}'
        education_heading = r'\cvsection{F19D}{Education}'
        self.assertIn(experience_heading, source)
        self.assertIn(education_heading, source)
        experience = source.split(experience_heading)[1].split(education_heading)[0]
        self.assertIn('2021–2022', experience)
        self.assertIn('2019–2021', experience)
        self.assertIn('DSVD chair', experience)
        self.assertIn('Magnet team', experience)
        self.assertNotIn('PhD in Computer Science', experience)
        self.assertNotIn('Recent highlights', source)
        self.assertNotIn('Yacine Belal wins', source)
        for logo in ['entpe.png', 'inria.jpg', 'insa.jpg', 'esi.png', 'lille.png']:
            self.assertIn(r'\cvlogo{assets/' + logo + '}', source)
        with tempfile.TemporaryDirectory() as folder:
            cv.stage_assets(Path(folder), page.root)
            for name in ['portrait.png', 'FontAwesome.otf', *cv.LOGOS]:
                self.assertTrue((Path(folder) / 'assets' / name).is_file(), name)


if __name__ == '__main__':
    unittest.main()
