"""Cross-file empirical lineage and numerical consistency, not absolute accuracy."""
from pathlib import Path
import json,hashlib,argparse
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/grid_calibration/merged4'
def read(p):return json.loads(p.read_text())
def main():
    global D
    ap=argparse.ArgumentParser();ap.add_argument('--extension',action='store_true');args=ap.parse_args()
    if args.extension:D=ROOT/'data/coverage_extension/calibration/merged4'
    checks=[('uncertainty','sources'),('magnitude','sources'),('panels','input_hashes')]
    if not args.extension:checks.insert(0,('diagnosis','sources'))
    for folder,key in checks:
        file='downstream_summary.json' if folder=='magnitude' else 'summary.json'
        for path,digest in read(D/folder/file).get(key,{}).items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
    loc=pd.read_csv(D/'panels/relocated.csv');base=pd.read_csv(D/'tomodd/round2_locations.csv');base=base[base.gap_deg<=300]
    assert set(loc.event_index)==set(base.event_index)
    assert np.array_equal(loc.depth_km.to_numpy(),base.depth_km.to_numpy())
    mag=pd.read_csv(D/'magnitude/magnitudes.csv');joined=loc.dropna(subset=['ML']).set_index('event_index')
    assert set(mag.event_index)<=set(loc.event_index)
    assert np.allclose(joined.ML,mag.set_index('event_index').loc[joined.index].ML)
    inv=read(D/'magnitude/magnitude_inversion_checks.json');assert all(r['rank']==r['events'] for r in inv['components'] if r['accepted'])
    edges=pd.read_csv(D/'magnitude/magnitude_edges.csv');measure=pd.read_csv(D/'magnitude/amplitude_measurements.csv');passing=measure[measure.snr_pass].set_index(['event_index','channel'])
    for r in edges.itertuples():
        a=passing.loc[(r.event_a,r.channel)];b=passing.loc[(r.event_b,r.channel)];assert min(a.snr_db,b.snr_db)>=5
        assert np.isclose(r.delta_M,np.log10(a.peak_velocity_m_s/b.peak_velocity_m_s))
    idx=pd.read_csv(D/'panels/cpoz_index.csv');picks=pd.read_csv(D/'tomodd/retained_picks.csv');waves=np.load(D/'panels/cpoz_gathers.npz')
    for r in idx.itertuples():
        own=picks[(picks.event_index==r.event_index)&picks.phase.eq('P')&picks.trace_id.str.contains('.CPOZ.',regex=False)]
        assert len(own)==1 and own.iloc[0].time==r.p_time and own.iloc[0].source==r.source
        assert waves[r.array_key].shape[1]==round(8*r.sample_rate_hz)
    svd=pd.read_csv(D/'uncertainty/regional_svd.csv');assert set(svd.event_index)<=set(loc.event_index)
    best=pd.read_csv(D/'panels/best_located.csv');assert (best.ncc_p+best.ncc_s>100).all()
    expected=loc[(loc.ncc_p+loc.ncc_s)>100];assert set(best.event_index)==set(expected.event_index)
    assert read(D/'focal/summary.json')['returncode']==0
    panels=read(ROOT/'docs/panel_record.json');layout=read(ROOT/'report/figure_layout.json')
    assert len(panels)==63 and len({r['panel'] for r in panels})==63
    assert [r['panel'] for r in panels if r['status']=='partially reproduced']==[x for f in layout for x in f['partial_panels']]
    for f in layout:
        for path in f['independent_files']:assert (ROOT/path).exists()
    result=dict(passed=True,empirical_locations=len(loc),own_magnitudes=len(mag),checked_amplitude_equations=len(edges),cpoz_traces=len(idx),svd_events=len(svd),S9_events=len(best),panels=len(panels),partial=sum(r['status']=='partially reproduced' for r in panels),scientific_catalog_accepted=False,
                scope='Tests saved source hashes, same-cohort identity, original P alignment, SNR/amplitude equations, selection counts and figure availability. Does not establish event identities, absolute depths, independent magnitude accuracy, reviewed polarities or exact reproduction.')
    (D.parent/'provisional_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
