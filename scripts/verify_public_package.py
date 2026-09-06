#!/usr/bin/env python3
"""Fail closed on binary assets and private values before publishing a text-only skill.

Keep --denylist JSON (a list of private strings) OUTSIDE the public repository.
Diagnostics report paths and categories only, never the matched private value.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import unicodedata

TEXT_SUFFIXES = {'.md', '.py', '.sh', '.json', '.yaml', '.yml', '.txt', '.toml'}
TEXT_NAMES = {'VERSION', 'LICENSE', '.gitignore', '.gitattributes'}
SKIP_DIRS = {'.git', '__pycache__', '.venv', 'venv', '.pytest_cache'}
SECRETS = [
    re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})'),
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    re.compile(r'/(?:Users|home)/[A-Za-z0-9_.-]+/'),
]


def normalize(text: str) -> str:
    text = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m[1], 16)), text)
    return unicodedata.normalize('NFKC', text).casefold()


def inspect_blob(name: str, raw: bytes, denied: list[str]) -> list[str]:
    errors = []
    path = Path(name)
    if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in TEXT_NAMES:
        errors.append('non-allowlisted-file')
    if any(part in {'fixed-documents', 'shared-materials', 'reference-samples'} for part in path.parts):
        errors.append('private-asset-directory')
    if '.private.' in path.name or '.local.' in path.name:
        errors.append('private-config')
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        return errors + ['non-text-content']
    if '\x00' in text:
        errors.append('binary-content')
    normalized = normalize(name + '\n' + text)
    if any(token in normalized for token in denied):
        errors.append('private-value')
    if any(pattern.search(text) for pattern in SECRETS):
        errors.append('secret-or-private-path')
    return errors


def git(root: Path, *args: str) -> bytes:
    return subprocess.check_output(['git', '-C', str(root), *args])


def load_history_exceptions(path: Path) -> dict[tuple[str, str, str], str]:
    """Accept reviewed immutable blobs, never paths, current files, or broad categories."""
    document = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(document, dict) or document.get('schema_version') != 1:
        raise ValueError('History exceptions require schema_version 1.')
    entries = document.get('exceptions')
    if not isinstance(entries, list):
        raise ValueError('History exceptions must contain an exceptions list.')
    exceptions = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError('Each history exception must be an object.')
        oid = entry.get('object')
        name = entry.get('path')
        error = entry.get('error')
        reason = entry.get('reason')
        if not isinstance(oid, str) or not re.fullmatch(r'[0-9a-f]{40}', oid):
            raise ValueError('Each history exception requires a full immutable Git blob ID.')
        if (not isinstance(name, str) or not name or Path(name).is_absolute()
                or '..' in Path(name).parts):
            raise ValueError('Each history exception requires an exact repository-relative path.')
        if error != 'private-value':
            raise ValueError('Only the reviewed private-value category can be excepted.')
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError('Each history exception requires a review reason.')
        key = (oid, name, error)
        if key in exceptions:
            raise ValueError('Duplicate history exception.')
        exceptions[key] = reason
    return exceptions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--denylist', type=Path, required=True)
    parser.add_argument('--history', action='store_true', help='Also inspect all reachable Git blobs.')
    parser.add_argument('--history-exceptions', type=Path,
                        help='Explicit reviewed exceptions for exact historical blobs only.')
    args = parser.parse_args()
    exceptions = {}
    if args.history_exceptions:
        if not args.history:
            parser.error('--history-exceptions requires --history.')
        try:
            exceptions = load_history_exceptions(args.history_exceptions)
        except (OSError, ValueError) as error:
            parser.error(str(error))
    root = args.root.resolve()
    denylist = args.denylist.resolve()
    if denylist.is_relative_to(root):
        parser.error('The private denylist must be stored outside the public repository.')
    values = json.loads(denylist.read_text(encoding='utf-8'))
    if not isinstance(values, list) or not values or any(not isinstance(v, str) or len(v) < 2 for v in values):
        parser.error('Provide a non-empty JSON list of private strings (minimum 2 characters).')
    denied = [normalize(v) for v in values]
    failures = []
    count = 0
    for path in sorted(root.rglob('*')):
        rel = path.relative_to(root)
        if any(p in SKIP_DIRS for p in rel.parts):
            continue
        if path.is_symlink():
            failures.append({'path': str(rel), 'errors': ['symlink-not-allowed']})
            continue
        if not path.is_file():
            continue
        count += 1
        errors = inspect_blob(str(rel), path.read_bytes(), denied)
        if errors:
            failures.append({'path': str(rel), 'errors': errors})
    history_count = 0
    applied_exceptions = []
    if args.history:
        objects = git(root, 'rev-list', '--objects', '--all').decode('utf-8').splitlines()
        for item in objects:
            oid, _, name = item.partition(' ')
            if git(root, 'cat-file', '-t', oid).strip() != b'blob':
                continue
            history_count += 1
            errors = inspect_blob(name, git(root, 'cat-file', 'blob', oid), denied)
            remaining_errors = []
            for error in errors:
                key = (oid, name, error)
                if key in exceptions:
                    applied_exceptions.append({'path': name, 'object': oid,
                                               'error': error, 'reason': exceptions[key]})
                else:
                    remaining_errors.append(error)
            errors = remaining_errors
            if errors:
                failures.append({'path': name, 'object': oid, 'errors': errors})
    print(json.dumps({'ok': not failures, 'files_checked': count,
                      'history_blobs_checked': history_count,
                      'history_exceptions_applied': len(applied_exceptions),
                      'history_exceptions': applied_exceptions, 'failures': failures},
                     ensure_ascii=False, indent=2))
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
