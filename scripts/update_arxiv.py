#!/usr/bin/env python3
"""Fetch this author's arXiv metadata using only Python's standard library."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time
import unicodedata
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ATOM = '{http://www.w3.org/2005/Atom}'
ARXIV = '{http://arxiv.org/schemas/atom}'
OPENSEARCH = '{http://a9.com/-/spec/opensearch/1.1/}'


def normalize(value):
    return re.sub('[^a-z0-9]', '', unicodedata.normalize('NFKD', value)
                  .encode('ascii', 'ignore').decode().lower())


def parse_feed(xml):
    feed = ET.fromstring(xml)
    if feed.tag != ATOM + 'feed':
        raise ValueError('Invalid arXiv feed')
    records = []
    for entry in feed.findall(ATOM + 'entry'):
        title = ' '.join(entry.findtext(ATOM + 'title', '').split())
        if entry.findtext(ATOM + 'id', '').endswith('/errors'):
            raise ValueError(title)
        authors = [a.findtext(ATOM + 'name', '') for a in entry.findall(ATOM + 'author')]
        if not any(normalize(author) == 'mohamedmaouche' for author in authors):
            continue
        identifier = re.sub(r'^https?://arxiv.org/abs/', '', entry.findtext(ATOM + 'id', ''))
        identifier = re.sub(r'v\d+$', '', identifier)
        if not re.fullmatch(r'(\d{4}\.\d{4,5}|[a-z.-]+/\d{7})', identifier):
            raise ValueError('Invalid arXiv identifier')
        record = {
            'title_s': [title], 'authFullName_s': authors, 'arxivId_s': identifier,
            'publicationDateY_i': int(entry.findtext(ATOM + 'published')[:4]),
        }
        doi = entry.findtext(ARXIV + 'doi')
        if doi:
            record['doiId_s'] = doi
        records.append(record)
    total = int(feed.findtext(OPENSEARCH + 'totalResults', '0'))
    return records, total


def fetch_records():
    records = []
    start = 0
    while True:
        query = urlencode({'search_query': 'au:"Mohamed Maouche"', 'start': start,
                           'max_results': 100, 'sortBy': 'submittedDate', 'sortOrder': 'descending'})
        request = Request('https://export.arxiv.org/api/query?' + query,
                          headers={'User-Agent': 'MohamedMaoucheWebsite/1.0 (mailto:mohamed.maouche@inria.fr)'})
        with urlopen(request, timeout=45) as response:
            batch, total = parse_feed(response.read())
        records.extend(batch)
        start += 100
        if start >= total:
            return records
        time.sleep(3.1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--feed', type=Path, help='Parse a downloaded Atom feed instead of calling the API')
    parser.add_argument('--output', type=Path, default=Path('assets/data/arxiv.json'))
    args = parser.parse_args()
    records = parse_feed(args.feed.read_bytes())[0] if args.feed else fetch_records()
    if not records:
        raise ValueError('No matching records; refusing to replace the previous data')
    payload = {'updated': datetime.now(timezone.utc).isoformat(), 'records': records}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix('.tmp')
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(args.output)
    print(f'Saved {len(records)} arXiv records to {args.output}')


if __name__ == '__main__':
    main()
