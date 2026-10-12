"""Inexpensive, read-only checks of existing results; writes only assessment/evidence.json.

No inference, association, inversion, downloads, or figure regeneration is run.
Run from the repository root: .venv/bin/python -B assessment/check_evidence.py
"""
from pathlib import Path
import hashlib
import json
import subprocess
import numpy as np
import pandas as pd
from pyproj import Geod

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'data/continuation'
read = lambda name: pd.read_csv(D / name, low_memory=False)
e, p, a = read('initial_events.csv'), read('picks.csv'), read('associations.csv')
s, c = read('sp_consistency.csv'), read('processed_coverage.csv')
assert a.pick_index.is_unique and a.pick_index.between(0, len(p)-1).all()
counts = a.groupby('event_index').size().reindex(e.event_index)
assert np.array_equal(counts, e.num_picks) and (counts >= 6).all()
assert p.probability.between(.3, 1).all()
assert not ((p.phase == 'S') & p.trace_id.str.split('.').str[1].isin(['CASE', 'CFB1', 'CFB3'])).any()
hours = 0.
for _, group in c.groupby('channel'):
    spans = []
    for start, end in sorted(zip(group.start, group.end)):
        if spans and start <= spans[-1][1] + .001:
            spans[-1][1] = max(end, spans[-1][1])
        else:
            spans.append([start, end])
    hours += sum(end-start for start, end in spans)/3600
requests = read('request_ledger.csv.gz')
assert (requests.loc[requests.status != 'downloaded', 'returned_channel_hours'] == 0).all()
m, edges, priors = read('magnitudes.csv').set_index('event_index'), read('magnitude_edges.csv'), read('routine_matches.csv')
gradient = {int(i): 0. for i in m.index}
for r in edges.itertuples():
    if r.event_a in gradient and r.event_b in gradient:
        residual = m.loc[r.event_a, 'ML'] - m.loc[r.event_b, 'ML'] - r.delta_M
        gradient[r.event_a] += r.weight*residual
        gradient[r.event_b] -= r.weight*residual
for r in priors.itertuples():
    if r.event_index in gradient and np.isfinite(r.Md):
        gradient[r.event_index] += m.loc[r.event_index, 'ML'] - r.Md
assert max(map(abs, gradient.values())) < 1e-7
manifest_ok, failures = 0, []
for line in (D/'manifest.sha256').read_text().splitlines():
    digest, name = line.split(maxsplit=1)
    file = ROOT / name.lstrip('*')
    if file.is_file() and hashlib.sha256(file.read_bytes()).hexdigest() == digest:
        manifest_ok += 1
    else:
        failures.append(name)
assert not failures
gnss = read('rite_gnss.csv')
context = json.loads((D/'context_summary.json').read_text())
gnss_checks = []
for tag, source, columns, offset in [
    ('17132077', 'RITE_daily.txt', ['mjd','raw_up','sigma'], context['gnss_datum_offset_m']),
    ('22259337', 'RITE_2000_2025.txt', ['mjd','n','e','raw_up','ns','es','sigma'], context['gnss2025_datum_offset_m'])]:
    raw = pd.read_csv(ROOT/'inputs/continuation'/source, sep=r'\s+', header=None, names=columns)
    joint = gnss[gnss.source.str.contains(tag)].merge(raw[['mjd','raw_up']], on='mjd')
    error = float(abs(joint.displacement_from_1905_m-joint.raw_up-offset).max())
    assert error < 1e-12
    gnss_checks.append(dict(source=source, rows=len(joint), max_abs_alignment_error_m=error))
vp = ROOT/'data/exploratory/velest_stability'
v32, v64 = pd.read_csv(vp/'locations_32.csv'), pd.read_csv(vp/'locations_64.csv')
assert np.array_equal(v32.event_index, v64.event_index)
_, _, horizontal_difference = Geod(ellps='WGS84').inv(v32.longitude.to_numpy(), v32.latitude.to_numpy(), v64.longitude.to_numpy(), v64.latitude.to_numpy())
precision = dict(
    model_tables_equal=pd.read_csv(vp/'model_32.csv').equals(pd.read_csv(vp/'model_64.csv')),
    max_depth_difference_km=float(abs(v32.depth_km-v64.depth_km).max()),
    max_horizontal_difference_m=float(horizontal_difference.max()),
    changed_horizontal_locations=int((horizontal_difference > 0).sum()),
    max_azimuthal_gap_difference_deg=int(abs(v32.azimuthal_gap_deg-v64.azimuthal_gap_deg).max()),
    scope='Saved precision only, not a new inversion or location-accuracy test.')
panels = json.loads((ROOT/'docs/panel_record.json').read_text())
chains = json.loads((D/'provenance_validation.json').read_text())['partial_panel_chains']
checked_paths = set()
for chain in chains:
    for name, digest in chain['saved_output_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest
        checked_paths.add(name)
    for key in ['plot', 'report_figure']:
        name = chain[key]
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == chain[key+'_sha256']
        checked_paths.add(name)
    for name in chain['input_files']:
        assert (ROOT/name).is_file(), name
        checked_paths.add(name)
result = dict(
    assessed_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    scope='Saved-table consistency, declared panel-file links and hashes; not a rerun or independent seismic validation.',
    events=len(e), picks=len(p), assigned_picks=len(a), phase_counts=p.phase.value_counts().to_dict(),
    assigned_phase_counts=a.merge(p,left_on='pick_index',right_index=True).phase.value_counts().to_dict(),
    events_by_day=e.time.str[:10].value_counts().sort_index().to_dict(),
    six_pick_events=int((e.num_picks == 6).sum()), all_s_events=int((e.num_p_picks == 0).sum()),
    depth_zero_events=int(np.isclose(e['z(km)'], 0).sum()), depth_eight_events=int(np.isclose(e['z(km)'], 8).sum()),
    depth_greater_3_7_km=int((e['z(km)'] > 3.7).sum()),
    depth_quantiles_km=e['z(km)'].quantile([0,.25,.5,.75,1]).to_dict(),
    processed_files=int(c.file.nunique()), channels=int(c.channel.nunique()), channel_hours=hours,
    request_status_counts=requests.status.value_counts().to_dict(),
    nonpositive_sp=int((s.observed_sp_s <= 0).sum()), sp_pairs=len(s),
    sp_residual_rms_s=float(np.sqrt(np.mean(s.residual_s**2))),
    magnitudes=len(m), magnitude_min=float(m.ML.min()), magnitude_max=float(m.ML.max()),
    magnitude_normal_equation_max_gradient=float(max(map(abs, gradient.values()))),
    gnss_source_alignment_checks=gnss_checks, velest_saved_precision_comparison=precision,
    manifest_matches=manifest_ok, partial_chains_hash_checked=len(chains),
    panel_count=len(panels), panel_status_counts=pd.Series([x['status'] for x in panels]).value_counts().to_dict(),
    inspected_panel_paths=sorted(checked_paths),
    not_checked=['Fresh empirical waveform processing', 'Manual phase/event validity',
                 'Absolute location accuracy', 'Instrument calibration accuracy',
                 'All raw-input hashes', 'All historical code paths or hidden inputs'])
(ROOT/'assessment/evidence.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k != 'inspected_panel_paths'}, indent=2))
