#!/usr/bin/env python3
"""Generate an academic LaTeX CV from this website and compile it locally."""
import argparse
from dataclasses import dataclass, field
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unicodedata
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
VOID_TAGS = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
             'link', 'meta', 'param', 'source', 'track', 'wbr'}
ESCAPES = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$',
           '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}',
           '~': r'\textasciitilde{}', '^': r'\textasciicircum{}'}
LOGOS = ('inria.jpg', 'insa.jpg', 'esi.png', 'lille.png', 'entpe.png', 'liris.png')


@dataclass
class Node:
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)

    def has_class(self, name):
        return name in self.attrs.get('class', '').split()

    def find_all(self, *, tag=None, cls=None, id=None):
        found = []
        for child in self.children:
            if isinstance(child, Node):
                if ((tag is None or child.tag == tag)
                        and (cls is None or child.has_class(cls))
                        and (id is None or child.attrs.get('id') == id)):
                    found.append(child)
                found.extend(child.find_all(tag=tag, cls=cls, id=id))
        return found

    def find(self, **kwargs):
        return next(iter(self.find_all(**kwargs)), None)


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node('document')
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def clean(value):
    return ' '.join(value.replace('\u200b', '').replace('—', '–').split())


def text(node):
    if node is None:
        return ''
    if isinstance(node, str):
        return node
    if node.has_class('fa'):
        return ''
    if node.tag == 'img':
        return node.attrs.get('alt', '')
    if node.tag == 'br':
        return ' · '
    return ''.join(text(child) for child in node.children)


def escape(value):
    return ''.join(ESCAPES.get(char, char) for char in clean(value))


def href(url, label):
    if urlparse(url).scheme not in {'https', 'http', 'mailto'}:
        return label
    url = quote(url, safe=':/?&=#%+@._~-')
    url = re.sub(r'([%&#_])', r'\\\1', url)
    return rf'\href{{{url}}}{{{label}}}'


def inline(node, omit=()):
    if node is None or any(node is excluded for excluded in omit):
        return ''
    if isinstance(node, str):
        # Retain spaces between inline elements, but escape their content.
        return re.sub(r'\s+', ' ', ''.join(ESCAPES.get(c, c) for c in node.replace('—', '–')))
    if node.has_class('fa') or node.tag in {'img', 'button', 'script', 'style'}:
        return ''
    if node.tag == 'br':
        return r'\enspace · \enspace '
    rendered = ''.join(inline(child, omit) for child in node.children)
    if node.tag == 'a':
        return href(node.attrs.get('href', ''), rendered)
    if node.tag in {'strong', 'b', 'em', 'i'}:
        return ('\\textbf' if node.tag in {'strong', 'b'} else '\\emph') + '{' + rendered + '}'
    if node.tag == 'p':
        return ' ' + rendered + ' '
    return rendered


def body_text(node):
    """Render paragraphs/lists, including closed disclosures, without site controls."""
    output = []
    for child in node.children:
        if not isinstance(child, Node):
            continue
        if child.tag == 'p':
            output.append(inline(child).strip() + '\n\n')
        elif child.tag in {'h3', 'h4'}:
            output.append(r'\cvgroup{' + inline(child).strip() + '}\n')
        elif child.tag in {'ul', 'ol'}:
            output.append('\\begin{itemize}\n')
            for item in child.children:
                if isinstance(item, Node) and item.tag == 'li':
                    paragraphs = [p for p in item.children if isinstance(p, Node) and p.tag == 'p']
                    rendered = inline(item, omit=paragraphs).strip()
                    if paragraphs:
                        rendered += ': ' + ' '.join(inline(p).strip() for p in paragraphs)
                    output.append('\\item ' + rendered + '\n')
            output.append('\\end{itemize}\n')
        elif child.tag in {'div', 'details'}:
            output.append(body_text(child))
    return ''.join(output)


def entry(date, title, content, logo=None):
    if logo in LOGOS:
        date += (r'\\[4pt]' if date else '') + rf'\cvlogo{{assets/{logo}}}'
    return f'\\cventry{{{date}}}{{{title}}}{{%\n{content.strip()}\n}}\n'


def institution_logo(node):
    source = node.attrs.get('data-cv-logo', '')
    if not source:
        images = node.find_all(tag='img')
        source = next((img.attrs.get('src', '') for img in images
                       if img.has_class('education-logo') or img.has_class('teaching-logo')), '')
    filename = Path(source).name
    return filename if filename in LOGOS else None


def past_experience(background):
    experiences = background.find_all(cls='past-experience')
    if not experiences:
        return '\n\n'.join(inline(p).strip() for p in background.find_all(tag='p')) + '\n'
    output = []
    for experience in experiences:
        match = re.match(r'(.+?) at (.+?) \((\d{4}[–-]\d{4})\)', clean(text(experience)))
        if not match:
            output.append(inline(experience).strip() + '\n\n')
            continue
        topic, _, period = match.groups()
        detail = inline(experience).strip()
        prefix = escape(topic) + ' at '
        if detail.startswith(prefix):
            detail = detail[len(prefix):]
        detail = detail.replace(f' ({period})', '', 1).rstrip('.') + '.'
        title = topic[0].upper() + topic[1:]
        output.append(entry(escape(period), escape(title), detail, institution_logo(experience)))
    return ''.join(output)


def grouped_entries(node, kind):
    output = []
    for child in node.children:
        if not isinstance(child, Node):
            continue
        if child.tag in {'h3', 'summary'}:
            output.append('\\cvgroup{' + inline(child).strip() + '}\n')
        elif child.tag == 'article':
            title = child.find(tag='h3') or child.find(tag='h4')
            date = child.find(cls='date') or child.find(cls='student-period')
            paragraphs = [p for p in child.children if isinstance(p, Node)
                          and p.tag == 'p' and p is not date]
            if kind == 'software':
                # Keep first-author contributor credits; code links are in the title.
                paragraphs.sort(key=lambda p: not p.has_class('software-contributor'))
            content = '\n\n'.join(inline(p).strip() for p in paragraphs)
            output.append(entry(escape(text(date)), inline(title).strip(), content, institution_logo(child)))
        elif child.tag in {'div', 'details'}:
            output.append(grouped_entries(child, kind))
        elif child.tag == 'ul':
            output.append(body_text(Node('div', children=[child])))
    return ''.join(output)


def normalize(value):
    return re.sub('[^a-z0-9]', '', unicodedata.normalize('NFKD', value)
                  .encode('ascii', 'ignore').decode().lower())


def first(value):
    return value[0] if isinstance(value, list) and value else value


def publication(record):
    title = first(record.get('title_s', []))
    authors = record.get('authFullName_s', [])
    if not title or not isinstance(authors, list):
        return None
    if not any(normalize(author) in {'mohamedmaouche', 'mmaouche'} for author in authors):
        return None
    hal = first(record.get('halId_s', ''))
    arxiv = re.sub(r'v\d+$', '', first(record.get('arxivId_s', '')) or '')
    doi = re.sub(r'^https?://(?:dx\.)?doi.org/', '', first(record.get('doiId_s', '')) or '', flags=re.I).lower()
    if re.fullmatch(r'(hal|tel)-\d+', hal or ''):
        url, rank = f'https://hal.science/{hal}', 0
    elif re.fullmatch(r'(\d{4}\.\d{4,5}|[a-z.-]+/\d{7})', arxiv, re.I):
        url, rank = f'https://arxiv.org/abs/{arxiv}', 1
    elif re.fullmatch(r'10\.\d{4,9}/\S+', doi):
        url, rank = f'https://doi.org/{doi}', 2
    else:
        return None
    keys = {f'title:{normalize(t)}' for t in record.get('title_s', [])}
    keys.update(f'{kind}:{identifier}' for kind, identifier in [('hal', hal), ('arxiv', arxiv.lower()), ('doi', doi)] if identifier)
    return dict(title=clean(title), authors=', '.join(authors).rstrip('.'),
                year=int(record.get('publicationDateY_i') or 0), url=url, rank=rank, keys=keys,
                venue=first(record.get('conferenceTitle_s')) or first(record.get('journalTitle_s')) or 'Preprint')


def saved_publications(page):
    records = []
    for article in page.find(id='publications').find_all(cls='publication'):
        anchor = article.find(tag='h3').find(tag='a')
        url = anchor.attrs['href']
        record = {'title_s': [clean(text(anchor))],
                  'authFullName_s': [clean(text(article.find(tag='p')))],
                  'publicationDateY_i': article.attrs.get('data-year'),
                  'journalTitle_s': clean(text(article.find(cls='venue')))}
        # Saved HTML author lists can be abbreviated; they are the site's trusted baseline.
        if '/hal.science/' in url:
            record['halId_s'] = url.rsplit('/', 1)[-1]
        elif 'arxiv.org/abs/' in url:
            record['arxivId_s'] = url.split('/abs/')[-1]
        elif 'doi.org/' in url:
            record['doiId_s'] = url.split('doi.org/')[-1]
        original_authors = record['authFullName_s'][0]
        record['authFullName_s'] = ['Mohamed Maouche']
        item = publication(record)
        if item:
            item['authors'] = original_authors.rstrip('.')
            records.append(item)
    return records


def fetch_hal():
    params = urlencode(dict(q='authFullName_s:"Mohamed Maouche"',
        fq='docType_s:(ART OR COMM OR UNDEFINED)',
        fl='halId_s,title_s,doiId_s,arxivId_s,authFullName_s,publicationDateY_i,conferenceTitle_s,journalTitle_s',
        rows=1000, wt='json'))
    request = Request('https://api.hal.science/search/?' + params,
                      headers={'User-Agent': 'MohamedMaoucheCV/1.0'})
    with urlopen(request, timeout=15) as response:
        return json.load(response)['response']['docs']


def merge_publications(saved, records):
    groups = list(saved)
    for record in records:
        incoming = publication(record)
        if not incoming:
            continue
        matches = [group for group in groups if group['keys'] & incoming['keys']]
        if matches:
            winner = min([*matches, incoming], key=lambda group: (group['rank'], group is not incoming))
            winner = {**winner, 'keys': set().union(incoming['keys'], *(group['keys'] for group in matches))}
            groups = [group for group in groups if not any(group is match for match in matches)]
            groups.append(winner)
        else:
            groups.append(incoming)
    return sorted(groups, key=lambda group: (-group['year'], group['title'].casefold()))


def render_publications(papers):
    output, current_year = [], None
    for index, paper in enumerate(papers, 1):
        if paper['year'] != current_year:
            current_year = paper['year']
            output.append('\\cvgroup{' + str(current_year) + '}\n')
        authors = escape(paper['authors'])
        authors = re.sub(r'(Mohamed Maouche|M\.\s?Maouche|M Maouche)', r'\\textbf{\1}', authors)
        venue = paper['venue']
        if str(current_year) not in venue:
            venue += f' · {current_year}'
        output.append(f'\\cvpublication{{{index}}}{{{href(paper["url"], escape(paper["title"]))}}}'
                      f'{{{authors}.}}{{{escape(venue)}}}\n')
    return ''.join(output)


def render_cv(page, papers):
    sections = []
    def add(icon, title, content):
        sections.append('\\cvsection{' + icon + '}{' + title + '}\n' + content)

    about = page.find(id='about').find(cls='section-body')
    profile = '\n\n'.join(inline(child).strip() for child in about.children
                          if isinstance(child, Node) and child.tag == 'p')
    interests = about.find(cls='research-grid')
    if interests:
        profile += '\n\n\\textbf{Research interests:} ' + '; '.join(
            escape(text(heading)) for heading in interests.find_all(tag='h3')) + '.\n'
    add('F007', 'Research profile', profile)

    background = about.find(tag='details')
    if background:
        add('F0B1', 'Past research experience', past_experience(background))
        content = ''
        for item in background.find_all(tag='li'):
            title = item.find(tag='strong')
            year = re.search(r'\b(?:19|20)\d{2}\b', text(item))
            detail = inline(item, omit=(title,)).strip().lstrip(' ·')
            if year:
                detail = re.sub(r',?\s*' + year[0] + r'\.', '.', detail, count=1)
            content += entry(year[0] if year else '', inline(title), detail, institution_logo(item))
        add('F19D', 'Education', content)

    add('F0C3', 'Research projects', grouped_entries(page.find(id='projects').find(cls='section-body'), 'projects'))
    add('F0C0', 'PhD supervision', grouped_entries(page.find(id='students').find(cls='section-body'), 'students'))
    add('F0F6', 'Publications and preprints', render_publications(papers))
    add('F19D', 'Teaching', grouped_entries(page.find(id='teaching').find(cls='section-body'), 'teaching'))
    add('F19C', 'Academic service', body_text(page.find(id='service').find(cls='section-body')))
    add('F121', 'Software', grouped_entries(page.find(id='software').find(cls='section-body'), 'software'))

    role = page.find(cls='role')
    contacts, email = [], ''
    for anchor in page.find(cls='profile-links').find_all(tag='a'):
        url = anchor.attrs.get('href', '')
        if url.startswith('mailto:'):
            email = href(url, escape(url[7:]))
        else:
            contacts.append(href(url, escape(text(anchor))))
    return {'NAME': escape(text(page.find(id='name'))), 'ROLE': escape(text(role)),
            'AFFILIATION': inline(page.find(cls='affiliation')).strip(),
            'EMAIL': email, 'CONTACTS': r' \enspace · \enspace '.join(contacts), 'CONTENT': '\n'.join(sections)}


def stage_assets(output_dir, page):
    """Keep the generated TeX and its local assets portable as a single folder."""
    assets = output_dir / 'assets'
    assets.mkdir(exist_ok=True)
    portrait = page.find(cls='portrait').find(tag='img').attrs['src']
    sources = {'portrait.png': ROOT / portrait,
               'FontAwesome.otf': ROOT / 'assets/plugins/font-awesome/fonts/FontAwesome.otf'}
    sources.update({name: ROOT / 'assets/images/logos' / name for name in LOGOS})
    for name, source in sources.items():
        shutil.copy2(source, assets / name)


def compile_pdf(tex_path, engine=None):
    choices = [engine] if engine else ['tectonic', str(ROOT / '.tools' / 'tectonic'), 'xelatex', 'lualatex']
    executable = next((shutil.which(choice) for choice in choices if shutil.which(choice)), None)
    if not executable:
        raise RuntimeError('No LaTeX engine found. Install Tectonic or XeLaTeX, or pass --engine /path/to/tectonic. '
                           'The generated .tex file is ready; --tex-only skips compilation.')
    executable = str(Path(executable).resolve())
    if 'tectonic' in Path(executable).name:
        command = [executable, '--untrusted', '--keep-logs', '--outdir', str(tex_path.parent), str(tex_path)]
        passes = 1
    else:
        command = [executable, '-no-shell-escape', '-interaction=nonstopmode', '-halt-on-error',
                   '-output-directory', str(tex_path.parent), str(tex_path)]
        passes = 2
    log = tex_path.with_suffix('.build.log')
    environment = dict(os.environ)
    if 'tectonic' in Path(executable).name:
        environment['XDG_CACHE_HOME'] = str(ROOT / '.tools/cache')
    with log.open('w') as handle:
        for _ in range(passes):
            result = subprocess.run(command, cwd=tex_path.parent, env=environment,
                                    stdout=handle, stderr=subprocess.STDOUT)
            if result.returncode:
                raise RuntimeError(f'LaTeX compilation failed. See {log}')
    pdf = tex_path.with_suffix('.pdf')
    if not pdf.is_file():
        raise RuntimeError(f'The compiler did not produce {pdf}. See {log}')
    return pdf


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html', type=Path, default=ROOT / 'index.html')
    parser.add_argument('--template', type=Path, default=ROOT / 'templates/academic-cv.tex')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'build/cv')
    parser.add_argument('--offline', action='store_true', help='Use saved HTML and the local arXiv feed; do not query HAL')
    parser.add_argument('--hal-json', type=Path, help='Use a saved HAL API response instead of querying HAL')
    parser.add_argument('--tex-only', action='store_true', help='Generate LaTeX without compiling')
    parser.add_argument('--engine', help='Path to Tectonic, XeLaTeX, or LuaLaTeX')
    args = parser.parse_args(argv)
    page = PageParser()
    page.feed(args.html.read_text(encoding='utf-8'))
    records = []
    feed = ROOT / 'assets/data/arxiv.json'
    if feed.exists():
        records.extend(json.loads(feed.read_text(encoding='utf-8'))['records'])
    if args.hal_json:
        records.extend(json.loads(args.hal_json.read_text(encoding='utf-8'))['response']['docs'])
    elif not args.offline:
        try:
            records.extend(fetch_hal())
        except (OSError, ValueError, KeyError) as error:
            print(f'Warning: HAL unavailable ({error}); using saved publications.', file=sys.stderr)
    papers = merge_publications(saved_publications(page.root), records)
    template = args.template.read_text(encoding='utf-8')
    for key, value in render_cv(page.root, papers).items():
        template = template.replace(f'@@{key}@@', value)
    args.output_dir = args.output_dir.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stage_assets(args.output_dir, page.root)
    tex_path = args.output_dir / 'Mohamed-Maouche-CV.tex'
    tex_path.write_text(template, encoding='utf-8')
    print(f'LaTeX: {tex_path} ({len(papers)} publications)')
    if not args.tex_only:
        print(f'PDF:   {compile_pdf(tex_path, args.engine)}')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError) as error:
        sys.exit(str(error))
