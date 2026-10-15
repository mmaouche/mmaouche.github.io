/* Merge live HAL records and the daily arXiv feed; preserve the saved list offline. */
(() => {
  'use strict';

  const section = document.querySelector('#publications');
  const body = section.querySelector('.section-body');
  const status = document.querySelector('#publications-status');
  const normalize = value => String(value).normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]/g, '');
  const first = value => Array.isArray(value) ? value[0] : value;

  // Repository links take precedence over publisher links.
  function preferredLink(record) {
    const hal = first(record.halId_s);
    if (/^(hal|tel)-\d+$/.test(hal || '')) return `https://hal.science/${hal}`;
    const arxiv = first(record.arxivId_s);
    if (/^(\d{4}\.\d{4,5}|[a-z.-]+\/\d{7})(v\d+)?$/i.test(arxiv || '')) {
      return `https://arxiv.org/abs/${arxiv}`;
    }
    const doi = first(record.doiId_s);
    if (/^10\.\d{4,9}\/\S+$/.test(doi || '')) return `https://doi.org/${doi}`;
    return null;
  }

  function articleFor(record, title, link) {
    const article = document.createElement('article');
    article.className = 'publication';
    article.dataset.year = Number(record.publicationDateY_i) || 0;
    const venue = document.createElement('span');
    venue.className = 'venue';
    venue.textContent = [first(record.conferenceTitle_s) || first(record.journalTitle_s)
      || 'Preprint', record.publicationDateY_i].filter(Boolean).join(' · ');
    const heading = document.createElement('h3');
    const anchor = document.createElement('a');
    anchor.href = link;
    anchor.textContent = title;
    heading.append(anchor);
    const authors = document.createElement('p');
    authors.textContent = (record.authFullName_s || []).join(', ');
    article.append(venue, heading, authors);
    return article;
  }

  // Sort the entire merged list, including records already in the saved HTML.
  function sortPublications() {
    const older = body.querySelector('.older-publications');
    const olderBody = older.querySelector('.detail-content');
    const articles = Array.from(body.querySelectorAll('.publication'));
    articles.sort((a, b) => {
      const yearDifference = (Number(b.dataset.year) || 0) - (Number(a.dataset.year) || 0);
      return yearDifference || a.querySelector('h3 a').textContent.localeCompare(
        b.querySelector('h3 a').textContent, 'en', { sensitivity: 'base' });
    });
    articles.forEach((article, index) => {
      if (index < 4) body.insertBefore(article, older);
      else olderBody.append(article);
    });
    older.hidden = articles.length <= 4;
  }

  const arxivId = value => String(first(value) || '')
    .replace(/^https?:\/\/(?:export\.)?arxiv\.org\/(?:abs|pdf)\//i, '')
    .replace(/\.pdf$/i, '').replace(/v\d+$/i, '').toLowerCase();
  const doiId = value => String(first(value) || '')
    .replace(/^https?:\/\/(?:dx\.)?doi\.org\//i, '').trim().toLowerCase();
  const linkRank = link => link.includes('hal.science/') ? 0
    : link.includes('arxiv.org/') ? 1 : 2;

  function recordKeys(record) {
    return [
      first(record.halId_s) && `hal:${first(record.halId_s)}`,
      first(record.arxivId_s) && `arxiv:${arxivId(record.arxivId_s)}`,
      first(record.doiId_s) && `doi:${doiId(record.doiId_s)}`,
      ...(record.title_s || []).map(title => `title:${normalize(title)}`)
    ].filter(Boolean);
  }

  // Rebuild identity groups on every merge, retaining aliases from both sources.
  function mergeRecords(records) {
    const groups = [];
    body.querySelectorAll('.publication').forEach(article => {
      const anchor = article.querySelector('h3 a');
      const url = anchor.href;
      const record = { title_s: [anchor.textContent] };
      const hal = url.match(/hal.science\/(hal-\d+)/);
      if (hal) record.halId_s = hal[1];
      else if (url.includes('arxiv.org/')) record.arxivId_s = arxivId(url);
      else if (url.includes('doi.org/')) record.doiId_s = doiId(url);
      const aliases = JSON.parse(article.dataset.identities || '[]');
      groups.push({ article, keys: new Set([...aliases, ...recordKeys(record)]) });
    });

    for (const record of records) {
      if (!Array.isArray(record.authFullName_s)
        || !record.authFullName_s.some(name => normalize(name) === 'mohamedmaouche')) continue;
      const title = first(record.title_s);
      const link = preferredLink(record);
      if (typeof title !== 'string' || !title.trim() || !link) continue;
      const keys = recordKeys(record);
      const matches = groups.filter(group => keys.some(key => group.keys.has(key)));
      let group;
      if (matches.length) {
        // HAL metadata and its year take precedence over arXiv's submission year.
        matches.sort((a, b) => linkRank(a.article.querySelector('h3 a').href)
          - linkRank(b.article.querySelector('h3 a').href));
        group = matches[0];
        for (const duplicate of matches.slice(1)) {
          duplicate.keys.forEach(key => group.keys.add(key));
          duplicate.article.remove();
          groups.splice(groups.indexOf(duplicate), 1);
        }
        const anchor = group.article.querySelector('h3 a');
        if (linkRank(link) <= linkRank(anchor.href)) {
          anchor.href = link;
          const year = Number(record.publicationDateY_i);
          if (year > 0) group.article.dataset.year = year;
        }
      } else {
        group = { article: articleFor(record, title, link), keys: new Set() };
        groups.push(group);
        body.insertBefore(group.article, body.querySelector('.older-publications'));
      }
      keys.forEach(key => group.keys.add(key));
      group.article.dataset.identities = JSON.stringify([...group.keys]);
    }
    sortPublications();
  }

  async function fetchHAL() {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const url = new URL('https://api.hal.science/search/');
      url.search = new URLSearchParams({
        q: 'authFullName_s:"Mohamed Maouche"',
        fq: 'docType_s:(ART OR COMM OR UNDEFINED)',
        fl: 'halId_s,title_s,doiId_s,arxivId_s,authFullName_s,publicationDateY_i,conferenceTitle_s,journalTitle_s',
        sort: 'publicationDateY_i desc,halId_s asc',
        rows: '1000', wt: 'json'
      });
      const response = await fetch(url, { signal: controller.signal, credentials: 'omit' });
      if (!response.ok) throw new Error(`HAL returned ${response.status}`);
      const data = await response.json();
      if (!Array.isArray(data.response?.docs)) throw new Error('Invalid HAL response');
      return data.response.docs;
    } finally {
      clearTimeout(timeout);
    }
  }

  async function fetchArxiv() {
    // The public site reads the updated repository feed directly: bot commits do
    // not trigger a GitHub Pages rebuild. Local previews use the bundled feed.
    const sources = location.hostname === 'mmaouche.github.io'
      ? ['https://raw.githubusercontent.com/mmaouche/mmaouche.github.io/master/assets/data/arxiv.json',
        'assets/data/arxiv.json']
      : ['assets/data/arxiv.json'];
    for (const source of sources) {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 10000);
      try {
        const response = await fetch(source, { signal: controller.signal,
          credentials: 'omit', cache: 'no-cache' });
        if (!response.ok) throw new Error(`arXiv feed returned ${response.status}`);
        const data = await response.json();
        if (!Array.isArray(data.records)) throw new Error('Invalid arXiv feed');
        return data;
      } catch (error) {
        // Try the bundled snapshot when the repository feed is unavailable.
      } finally {
        clearTimeout(timeout);
      }
    }
    throw new Error('arXiv feed unavailable');
  }

  async function refresh() {
    status.textContent = 'Loading publications from HAL and the arXiv feed…';
    const available = [];
    const unavailable = [];
    const updateStatus = () => {
      status.textContent = [available.length ? `Publications: ${available.join('; ')}.` : '',
        unavailable.length ? `Unavailable: ${unavailable.join(', ')}; saved papers are retained.` : '']
        .filter(Boolean).join(' ');
    };
    // Render each source as soon as it returns, even if the other source fails.
    await Promise.allSettled([
      (async () => {
        try {
          mergeRecords(await fetchHAL());
          available.push('HAL live');
        } catch (error) {
          console.error('HAL publication update failed:', error);
          unavailable.push('HAL');
        }
        updateStatus();
      })(),
      (async () => {
        try {
          const data = await fetchArxiv();
          mergeRecords(data.records);
          const date = new Date(data.updated);
          const label = Number.isNaN(date.getTime()) ? '' : ` (${date.toLocaleDateString('en-GB')})`;
          available.push(`arXiv daily feed${label}`);
        } catch (error) {
          console.error('arXiv publication update failed:', error);
          unavailable.push('arXiv');
        }
        updateStatus();
      })()
    ]);
  }

  sortPublications();
  refresh();
})();
