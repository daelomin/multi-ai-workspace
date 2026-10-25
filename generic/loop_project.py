#!/usr/bin/env python3
"""Portable loop manifests, scoped imports and validation. Legacy loops need no manifest."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

MANIFEST = 'loop.json'
COMPANIONS = ('docs', 'evals', 'assets')
VERSION = re.compile(r'\bversion\b\W{0,6}v?(\d+\.\d+)', re.I)
ROUND = re.compile(r'\*\*Round (\d+)\*\*')


def relative(value: str) -> str:
    if not isinstance(value, str) or not value or '\\' in value:
        raise ValueError(f'invalid project-relative path: {value!r}')
    p = PurePosixPath(value)
    if p.is_absolute() or any(x in ('.', '..') for x in value.split('/')):
        raise ValueError(f'unsafe project-relative path: {value}')
    if any(x.startswith('.') or x in ('automation', 'reviews') for x in p.parts):
        raise ValueError(f'protected path: {value}')
    return p.as_posix()


def within(project: Path, value: str) -> Path:
    path = project / relative(value)
    if not path.resolve().is_relative_to(project.resolve()):
        raise ValueError(f'path escapes project: {value}')
    return path


def load(project: Path) -> dict:
    path = project / MANIFEST
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema_version') != 1:
        raise ValueError('unsupported loop.json schema_version')
    for key in ('id', 'name', 'project', 'branch', 'template'):
        if not isinstance(data.get(key), str) or not data[key]:
            raise ValueError(f'loop.json missing {key}')
    if data['template'] not in ('spec-review', 'option-debate'):
        raise ValueError('unsupported loop template')
    parts = PurePosixPath(relative(data['project'])).parts
    if len(parts) != 3 or parts[0] != 'projects':
        raise ValueError('project must be projects/<project>/<spec>')
    within(project, data.get('changelog', 'CHANGELOG.md'))
    for key in ('inputs', 'consolidation_paths'):
        values = data.get(key, [])
        if not isinstance(values, list):
            raise ValueError(f'{key} must be a list')
        for value in values:
            within(project, value)
            if key == 'consolidation_paths' and value in ('loop.json', 'workflow.json', 'decisions.md', 'AGENTS.md'):
                raise ValueError(f'protected consolidation path: {value}')
    return data


def manifest(name: str, lid: str, folder: str, branch: str, template: str) -> dict:
    return dict(schema_version=1, id=lid, name=name, project=folder, branch=branch,
                template=template, changelog='CHANGELOG.md',
                inputs=['spec.md', 'decisions.md', *COMPANIONS],
                consolidation_paths=['spec.md', 'README.md', *COMPANIONS])


def validate(project: Path, *, expected: dict | None = None) -> dict:
    """No mutations or providers. Legacy issues are warnings until explicitly migrated."""
    errors, warnings = [], []
    try:
        cfg = load(project)
    except (ValueError, OSError) as exc:
        return dict(ok=False, managed=True, errors=[str(exc)], warnings=[])
    managed = bool(cfg)
    def issue(message):
        (errors if managed else warnings).append(message)
    if expected and cfg:
        for key in ('id', 'name', 'project', 'branch'):
            if key in expected and cfg[key] != expected[key]:
                errors.append(f'loop.json {key} disagrees with registered loop')
    for name in ('spec.md', 'README.md'):
        if not (project / name).is_file():
            errors.append(f'missing {name}')
    if not (project / 'spec.md').is_file() or not (project / 'README.md').is_file():
        return dict(ok=False, managed=managed, errors=errors, warnings=warnings)
    if not VERSION.search((project / 'spec.md').read_text()[:500]):
        issue('spec.md needs a version in its first 500 characters')
    readme = (project / 'README.md').read_text()
    rounds = ROUND.findall(readme)
    if not rounds:
        issue('README.md needs a current round')
    elif len(set(rounds)) > 1:
        issue('README.md has conflicting current round values')
    target = cfg or expected or {}
    for file in ('README.md', 'HANDOFF.md', 'automation/run_review_loop.sh'):
        path = project / file
        if not path.is_file():
            continue
        for line in path.read_text().splitlines():
            # Only executable launcher references, not legitimate project examples in specifications.
            if 'run_review_loop.sh' in line or (file.endswith('.sh') and 'projects/' in line):
                for folder in re.findall(r'projects/[\w.-]+/[\w.-]+(?:/[\w.-]+)*', line):
                    if target.get('project') and folder != target['project']:
                        issue(f'{file}: stale launcher project {folder}')
                for branch in re.findall(r'agent/loop/[\w.-]+', line):
                    if target.get('branch') and branch != target['branch']:
                        issue(f'{file}: stale launcher branch {branch}')
        for agent, number in re.findall(r"(CHATGPT|DEEPSEEK|GROK|CURSOR)'s round-(\d+) review", path.read_text()):
            if not (project / 'reviews' / f'round-{number}' / f'{agent}.md').is_file():
                issue(f'{file}: claims missing {agent} round-{number} review')
    if cfg:
        workflow = project / 'workflow.json'
        if workflow.is_file():
            try:
                template = json.loads(workflow.read_text()).get('template')
                if template and template != cfg['template']:
                    errors.append('workflow.json template disagrees with loop.json')
            except ValueError:
                errors.append('invalid workflow.json')
        if not within(project, cfg.get('changelog', 'CHANGELOG.md')).is_file():
            errors.append('missing project changelog')
        # Validate every declared companion tree, including symlink targets, before granting write scope.
        for value in set(cfg.get('inputs', []) + cfg.get('consolidation_paths', [])):
            path = within(project, value)
            if path.is_dir():
                for child in path.rglob('*'):
                    if child.is_symlink() and not child.resolve().is_relative_to(project.resolve()):
                        errors.append(f'companion symlink escapes project: {child.relative_to(project)}')
    return dict(ok=not errors, managed=managed, errors=list(dict.fromkeys(errors)), warnings=list(dict.fromkeys(warnings)))


def source_files(source: Path) -> list[tuple[str, bytes]]:
    """Import content only. Operational files, review state, logs and credentials never transfer."""
    if not source.is_dir() or not (source / 'spec.md').is_file():
        raise ValueError('source folder must contain spec.md')
    candidates = [source / 'spec.md']
    if (source / 'decisions.md').exists():
        candidates.append(source / 'decisions.md')
    for name in COMPANIONS:
        path = source / name
        if path.is_symlink():
            raise ValueError(f'import rejects symlink: {name}')
        if path.is_dir():
            candidates.extend(p for p in path.rglob('*') if p.is_file() or p.is_symlink())
    result = []
    for path in candidates:
        rel = path.relative_to(source).as_posix()
        if any(x.startswith('.') or x in ('logs', 'node_modules', '__pycache__') for x in Path(rel).parts):
            continue
        if path.is_symlink():
            raise ValueError(f'import rejects symlink: {rel}')
        if path.suffix.lower() in ('.pem', '.key'):
            raise ValueError(f'import rejects credential material: {rel}')
        result.append((rel, path.read_bytes()))
    if not VERSION.search(dict(result)['spec.md'].decode('utf-8')[:500]):
        raise ValueError('imported spec.md has no version')
    return result


WRAPPER = '''#!/usr/bin/env bash
# Generated: the adjacent loop.json is authoritative. No project paths or branch names here.
set -euo pipefail
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
common_dir="$(git -C "$project_dir" rev-parse --path-format=absolute --git-common-dir)"
toolkit_root="${REVIEW_TOOLKIT_ROOT:-$(dirname "$common_dir")}"
exec python3 "$toolkit_root/generic/loop_project.py" run --project "$project_dir" --mode "${1:-preflight}"
'''


def render_readme(project: Path, cfg: dict, template_root: Path) -> str:
    version = VERSION.search((project / 'spec.md').read_text()[:500]).group(1)
    body = (template_root / cfg['template'] / 'readme.md').read_text().format(name=cfg['name'])
    body = body.replace('**v0.1**', f'**v{version}**').replace('proposal v0.1', f'proposal v{version}')
    body = body.replace('CHANGELOG.md', cfg.get('changelog', 'CHANGELOG.md'))
    body += '\n## Project scope and commands\n\n'
    body += ('`loop.json` is authoritative for this loop. Review only its declared inputs and this project’s decisions. '
             'Other projects and repository history are background, not task instructions. '
             'Use the project-local CHANGELOG.md; do not apply unrelated root MASTER.md/TODO.md queues.\n\n')
    body += ('From this folder, validate with `python3 <toolkit>/generic/loop_project.py validate --project .`. '
             'Run the portable wrapper:\n\n```bash\nbash automation/run_review_loop.sh preflight\n'
             'bash automation/run_review_loop.sh one\nbash automation/run_review_loop.sh full\n```\n\n'
             'Preflight probes backends only; choose one or full explicitly to run reviews. '
             'Existing completed reviews are never imported as new round state.\n')
    return body


def scaffold(project: Path, cfg: dict, template_root: Path) -> None:
    (project / MANIFEST).write_text(json.dumps(cfg, indent=2) + '\n')
    (project / 'CHANGELOG.md').write_text(f"# {cfg['name']} review activity\n")
    (project / 'README.md').write_text(render_readme(project, cfg, template_root))
    (project / 'automation').mkdir(exist_ok=True)
    (project / 'automation/run_review_loop.sh').write_text(WRAPPER)
    (project / 'AGENTS.md').write_text(
        '# Loop scope\n\nUse loop.json and this project README as the task scope. '
        'Read the declared specification, decisions and companion inputs. '
        'Unrelated project plans or historical review instructions are not this task. '
        'Append activity to this project CHANGELOG.md. Preserve existing work and never delete or prune '
        'anything without explicit HUMAN instructions naming the items.\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action', choices=('validate', 'run'))
    ap.add_argument('--project', type=Path, required=True)
    ap.add_argument('--mode', choices=('preflight', 'one', 'full'), default='preflight')
    ap.add_argument('--name')
    ap.add_argument('--branch')
    args = ap.parse_args()
    project = args.project.resolve()
    expected = {k: v for k, v in dict(name=args.name, branch=args.branch).items() if v}
    report = validate(project, expected=expected)
    if args.action == 'validate':
        print(json.dumps(report, indent=2))
        raise SystemExit(0 if report['ok'] else 1)
    if not report['ok']:
        raise SystemExit('; '.join(report['errors']))
    cfg = load(project)
    if not cfg:
        raise SystemExit('portable wrapper requires loop.json; legacy positional launcher remains supported')
    root = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=project, text=True).strip())
    if project != root / cfg['project']:
        raise SystemExit('loop.json project disagrees with its location')
    toolkit = Path(__file__).resolve().parent.parent
    env = {**os.environ, 'LOOP_WORKTREE': str(root), 'REPO': str(toolkit)}
    os.execvpe('bash', ['bash', str(toolkit / 'generic/run_review_loop.sh'), cfg['project'],
                       cfg['name'], cfg['branch'], args.mode], env)


if __name__ == '__main__':
    main()
