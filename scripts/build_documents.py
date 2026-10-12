"""Build presentation only, using saved results; never run scientific processing.

Published PDF crops are display-only references in comparison.pdf. No pixels,
coordinates or numerical values from those images enter an analysis or plot.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import os
import re
import subprocess

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
REPORT = ROOT / 'report'
TMP = ROOT / 'tmp' / 'report-layout'
DPI = 200
ORDER = ['1', '2', '3', '4'] + ['S' + str(i) for i in range(1, 16)]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tex(value):
    replacements = {'&': r'\&', '%': r'\%', '_': r'\_', '#': r'\#'}
    return ''.join(replacements.get(c, c) for c in value)


def run(command, logs):
    result = subprocess.run(command, capture_output=True, text=True)
    logs.append(dict(command=command, returncode=result.returncode,
                     output=result.stdout + result.stderr))
    (REPORT / 'document_build_log.json').write_text(json.dumps(logs, indent=2) + '\n')
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout


def reference_crop(item, logs):
    """Crop only the published figure area; trim blank margins for display."""
    x0, y0, x1, y1 = item['crop_points']
    scale = DPI / 72
    x, y = math.floor(x0 * scale), math.floor(y0 * scale)
    width = math.ceil(x1 * scale) - x
    height = math.ceil(y1 * scale) - y
    target = REPORT / 'reference_assets' / ('F' + item['figure'])
    run(['pdftoppm', '-f', str(item['page']), '-l', str(item['page']),
         '-r', str(DPI), '-x', str(x), '-y', str(y), '-W', str(width),
         '-H', str(height), '-singlefile', '-png', item['source'], str(target)], logs)
    path = target.with_suffix('.png')
    with Image.open(path) as image:
        image = image.convert('RGB')
        difference = ImageChops.difference(image, Image.new('RGB', image.size, 'white'))
        bounds = difference.convert('L').point(lambda v: 255 if v > 12 else 0).getbbox()
        assert bounds, item['figure']
        left, top, right, bottom = bounds
        bounds = (max(0, left-8), max(0, top-8), min(image.width, right+8), min(image.height, bottom+8))
        image.crop(bounds).save(path)
    return {'figure': item['figure'], 'source': item['source'],
            'source_sha256': digest(item['source']), 'page': item['page'],
            'crop_points': item['crop_points'], 'display_dpi': DPI,
            'file': str(path.relative_to(ROOT)), 'sha256': digest(path),
            'role': 'Published reference; comparison PDF only; no analytical input'}


def paper_figure(item):
    if not item['independent_files']:
        return r'\paragraph{Figure '+item['figure']+r' --- not reproduced.} '+tex(item['missing'])+'\n'
    number=int(item['figure'].replace('S',''))
    lines = [r'\setcounter{figure}{'+str(number-1)+'}',r'\begin{figure}[H]', r'\centering']
    for panel, path in zip(item.get('file_labels',item['partial_panels']), item['independent_files']):
        lines += [r'\par\smallskip\textbf{Panel ' + tex(panel) + r': partially reproduced}\par',
                  r'\includegraphics[width=.94\linewidth,height=.66\textheight,keepaspectratio]{' + path + '}']
    if item['missing']:
        lines += [r'\par\small '+tex(item['missing'])]
    lines += [r'\caption{' + tex(item['title'] + '. ' + item['caption']) + '}',
              r'\label{publication:' + item['figure'] + '}', r'\end{figure}']
    return '\n'.join(lines) + '\n'


def comparison_page(item):
    figure = item['figure']
    lines = [r'\pdfbookmark[0]{Figure ' + figure + '}{comparison:' + figure + '}',
             r'{\Large\bfseries Figure ' + figure + ': ' + tex(item['title']) + r'}\par\medskip',
             r'\begin{minipage}[t]{.485\textwidth}\vspace{0pt}\centering',
             r'{\large\bfseries Published reference}\par\medskip',
             r'\includegraphics[width=\linewidth,height=5.85in,keepaspectratio]{report/reference_assets/F' + figure + r'.png}',
             r'\par\smallskip{\footnotesize Tan et al. (2025), ' + tex(item['source']) + ', p. ' + str(item['page']) + r'.\par DOI: 10.1126/science.adw9038.}',
             r'\end{minipage}\hfill', r'\begin{minipage}[t]{.485\textwidth}\vspace{0pt}\centering',
             r'{\large\bfseries Independent result}\par\medskip']
    for panel, path in zip(item.get('file_labels',item['partial_panels']), item['independent_files']):
        lines += [r'\textbf{Panel ' + tex(panel) + r' --- partially reproduced}\par\smallskip',
                  r'\includegraphics[width=\linewidth,height=4.3in,keepaspectratio]{' + path + '}',
                  r'\par\smallskip{\small ' + tex(item['caption']) + r'}\par\medskip']
    if item['missing']:
        label = 'Panels A and C' if figure == '1' else ('Panels A, B and D' if figure == 'S15' else 'All panels/views')
        lines += [r'\unavailable{' + label + '}{' + tex(item['missing']) + '}']
    lines += [r'\end{minipage}', r'\vfill', r'\newpage']
    return '\n'.join(lines) + '\n'


def verify(layout):
    text = subprocess.check_output(['pdftotext', '-layout', 'report/report.pdf', '-'], text=True)
    flat = ' '.join(text.split())
    supplement = flat.index('Reproduced supplement')
    documentation = flat.index('Reproduction documentation')
    assert supplement < documentation
    sections = ['The current phase of unrest', 'Improving the earthquake catalog',
                'A clearer view of the current phase of unrest',
                'Implications for the physical process driving the unrest',
                'New perspectives for improved seismic risk assessment']
    positions = [flat.index(s) for s in sections]
    assert positions == sorted(positions) and positions[-1] < supplement
    supplemental_sections = ['Building the Campi Flegrei high-resolution earthquake catalog',
                             'Validation of earthquake locations',
                             'Template Matching to Detect Hybrid Events']
    positions = [flat.index(s, supplement) for s in supplemental_sections]
    assert positions == sorted(positions) and positions[-1] < documentation
    captions = re.findall(r'Figure\s+(S?\d+):', flat[:documentation])
    expected=[item['figure'] for item in layout if item['independent_files']]
    assert captions == expected, captions
    assert re.findall(r'Figure\s+(S?\d+):', flat[:supplement]) == [f for f in expected if not f.startswith('S')]
    assert r'\missingresult' not in ''.join((REPORT/'figure_sections'/('F'+f+'.tex')).read_text() for f in ORDER)
    assert 'Table S1:' in flat[supplement:documentation] and 'Table S2:' in flat[supplement:documentation]
    for audit in ['Scientific specification and input verification', 'Data access and actual coverage',
                  'Independent processing and explicit departures', 'Figure-by-figure record',
                  'Saved numerical tables and equation consistency checks']:
        assert flat.index(audit) > documentation, audit
    assert 'No publication panel is fully independently reproduced' in flat
    paper_inputs = (REPORT / 'report.fls').read_text()
    assert 'reference_assets' not in paper_inputs
    for source in ['tanmodel.pdf', 'tanmodelsupp.pdf']:
        assert source not in paper_inputs
    # No unrelated graphics can appear in the main paper or reproduced supplement.
    for source in ['main_paper.tex', 'reproduced_supplement.tex']:
        assert r'\includegraphics' not in (REPORT / source).read_text()
    for item in layout:
        fragment = (REPORT / 'figure_sections' / ('F' + item['figure'] + '.tex')).read_text()
        assert re.findall(r'\\includegraphics\[[^\]]*\]\{([^}]+)\}', fragment) == item['independent_files']

    comparison = subprocess.check_output(['pdftotext', '-layout', 'report/comparison.pdf', '-'], text=True)
    pages = [page for page in comparison.split('\f') if page.strip()]
    assert len(pages) == len(ORDER), len(pages)
    for page, figure in zip(pages, ORDER):
        normalized = ' '.join(page.split())
        assert normalized.startswith('Figure ' + figure + ':'), normalized[:90]
        assert normalized.count('Published reference') == 1
        assert normalized.count('Independent result') == 1
        assert 'Reproduction documentation' not in normalized
        assert 'Reproduction diagnostic' not in normalized
    comparison_inputs = (REPORT / 'comparison.fls').read_text()
    allowed_results = {path for item in layout for path in item['independent_files']}
    for path in Path('figures').glob('*.pdf'):
        if str(path) not in allowed_results:
            assert str(path) not in comparison_inputs, str(path)
    page_sections = {}
    for heading in ['Main paper', 'Reproduced supplement', 'Reproduction documentation']:
        page_sections[heading] = next(i for i, page in enumerate(text.split('\f'), 1) if heading in ' '.join(page.split()))
    return dict(main_section_order=sections, supplement_section_order=supplemental_sections,
                publication_figure_order=captions, comparison_pages=len(pages),
                report_pages=len([p for p in text.split('\f') if p.strip()]), section_pages=page_sections,
                published_images_only_in_comparison=True, unrelated_comparison_figures=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clean', action='store_true', help='Remove and regenerate document products only.')
    args = parser.parse_args()
    TMP.mkdir(parents=True, exist_ok=True)
    (REPORT / 'reference_assets').mkdir(exist_ok=True)
    (REPORT / 'figure_sections').mkdir(exist_ok=True)
    os.environ.update(TMPDIR=str(ROOT / 'tmp'), SOURCE_DATE_EPOCH='1791763200',
                      PYTHONDONTWRITEBYTECODE='1')
    baseline = json.loads((REPORT / 'layout_baseline.json').read_text())
    baseline_now = {p: digest(p) for p in baseline['files'] if Path(p).exists()}
    historical_match = baseline_now == baseline['files']
    removed_since_baseline = sorted(set(baseline['files'])-set(baseline_now))
    # The authorized continuation adds scientific products beyond the earlier
    # presentation baseline. Protect the current scientific files too.
    protected=set(baseline_now)
    for directory in ['data','figures','scripts','config']:
        protected.update(str(p) for p in Path(directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    before = {p: digest(p) for p in sorted(protected)}
    layout = json.loads((REPORT / 'figure_layout.json').read_text())
    assert [item['figure'] for item in layout] == ORDER
    rows = json.loads((ROOT / 'docs/panel_record.json').read_text())
    assert sorted(panel for item in layout for panel in item['panels']) == sorted(r['panel'] for r in rows)
    partial = [r['panel'] for r in rows if r['status'] == 'partially reproduced']
    assert partial == [panel for item in layout for panel in item['partial_panels']]
    assert all((ROOT/path).exists() for item in layout for path in item['independent_files'])
    for item in json.loads((ROOT / 'docs/file_inventory.json').read_text()):
        if item['file'].endswith('.pdf'):
            assert digest(item['file']) == item['sha256'], item['file']
    if args.clean:
        for name in ['report', 'comparison']:
            for extension in ['pdf', 'aux', 'log', 'out', 'fls']:
                (REPORT / (name + '.' + extension)).unlink(missing_ok=True)
        for directory, suffix in [('reference_assets', '*.png'), ('figure_sections', '*.tex')]:
            for path in (REPORT / directory).glob(suffix):
                path.unlink()
    logs, crops = [], []
    for item in layout:
        crops.append(reference_crop(item, logs))
        (REPORT / 'figure_sections' / ('F' + item['figure'] + '.tex')).write_text(paper_figure(item))
    (REPORT / 'reference_crops.json').write_text(json.dumps(crops, indent=2) + '\n')
    (REPORT / 'comparison_pages.tex').write_text(''.join(comparison_page(item) for item in layout))
    for name in ['report', 'comparison']:
        for iteration in range(2):
            print('Compiling', name, 'pass', iteration + 1, flush=True)
            run(['pdflatex', '-interaction=nonstopmode', '-halt-on-error', '-recorder',
                 '-output-directory=report', 'report/' + name + '.tex'], logs)
        warnings = [line for line in (REPORT / (name + '.log')).read_text().splitlines()
                    if 'Overfull' in line or 'LaTeX Warning' in line or 'pdfTeX warning' in line or 'Package hyperref Warning' in line]
        assert not warnings, '\n'.join(warnings)
    verification = verify(layout)
    after = {p: digest(p) for p in before}
    assert after == before, 'Document build changed protected analysis files.'
    outputs = {str(p.relative_to(ROOT)): digest(p) for p in REPORT.rglob('*')
               if p.is_file() and p.suffix in ['.tex', '.pdf', '.png', '.json']
               and p.name not in ['document_build.json', 'document_build_log.json']}
    verification.update(build_passed=True, analysis_executed=False,
                        protected_files_checked=len(before), protected_files_unchanged=True,
                        matches_pre_edit_snapshot=historical_match,
                        removed_since_historical_baseline=removed_since_baseline,
                        partial_panels=partial, independently_reproduced_panels=[],
                        panels_without_valid_independent_comparison=[r['panel'] for r in rows if r['status'] == 'not reproduced'],
                        source_and_output_sha256=outputs)
    (REPORT / 'document_build.json').write_text(json.dumps(verification, indent=2) + '\n')
    print(json.dumps({k: v for k, v in verification.items() if k != 'source_and_output_sha256'}, indent=2))


if __name__ == '__main__':
    main()
