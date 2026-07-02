#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_all_links.py — 台帳(topics_master.json)の全sources_fukuroi URLの生存確認のみを行う
（本文突合はしない、verify_sources.pyより軽量なリンク切れ検出専用ツール）。

実行: python3 scripts/check_all_links.py
出力: reports/link-check-YYYYMMDD.md
"""
import json, time, urllib.request, urllib.error
from datetime import date
from pathlib import Path

LEDGER = Path('data/topics_master.json')
REPORT_DIR = Path('reports')
UA = 'enshu-lifehack-verify/1.0 (+https://fukuroi.enshu-lifehack.com/)'
WAIT = 0.4


def fetch_status(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.status, r.geturl()
        except urllib.error.HTTPError as e:
            return e.code, url
        except Exception as e:
            if attempt == 0:
                time.sleep(2); continue
            return 0, str(e)


def main():
    ledger = json.loads(LEDGER.read_text(encoding='utf-8'))
    url_items = {}
    for item in ledger:
        for s in item.get('sources_fukuroi', []):
            url_items.setdefault(s['url'], []).append((item['href'], s.get('label', '')))

    cache = {}
    bad = []
    total = len(url_items)
    for i, url in enumerate(sorted(url_items), 1):
        if url not in cache:
            cache[url] = fetch_status(url)
            time.sleep(WAIT)
        status, final = cache[url]
        print(f'[{i}/{total}] {status} {url}')
        if status != 200:
            bad.append((url, status, url_items[url]))

    REPORT_DIR.mkdir(exist_ok=True)
    today = str(date.today())
    lines = [f'# リンク切れチェック {today}', '',
             f'対象URL数: {total} ／ NG: {len(bad)}', '']
    for url, status, refs in bad:
        lines.append(f'## {status}: {url}')
        for href, label in refs:
            lines.append(f'- {href} 「{label}」')
        lines.append('')
    out = REPORT_DIR / f'link-check-{today}.md'
    out.write_text('\n'.join(lines), encoding='utf-8')
    print(f'\nNG {len(bad)}/{total} -> {out}')


if __name__ == '__main__':
    main()
