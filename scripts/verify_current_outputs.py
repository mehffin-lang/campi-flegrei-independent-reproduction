"""Check the explicit current data/plot/report graph and saved-result invariants.

This does not prove that no unexamined or hidden source influenced prior work.
It verifies the files, commands, exclusions and numerical identities listed here.
"""
from pathlib import Path
import hashlib,json,subprocess,sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/continuation'

def sha(name):return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()

def main():
    # This isolated synthetic association test writes only tests/results. It is
    # not a source for any empirical table or figure checked below.
    subprocess.run([sys.executable,'scripts/validate_association.py'],cwd=ROOT,check=True)
    rows=json.loads((ROOT/'docs/panel_record.json').read_text());chains=[]
    for r in rows:
        if r['status']!='partially reproduced':continue
        saved=[p.strip() for p in r['saved_data'].split(';')]
        inputs=r['input_observation_files']
        assert all('quarantine/' not in p and 'science.adw9038' not in p and 'reference_assets' not in p and 'tests/' not in p for p in inputs+saved)
        assert r['data_command'] and r['plot_command']
        chains.append(dict(panel=r['panel'],input_files=inputs,saved_output_sha256={p:sha(p) for p in saved},
                           data_command=r['data_command'],plot_command=r['plot_command'],plot=r['generated_figure'],plot_sha256=sha(r['generated_figure']),
                           report_figure=r['report_figure'],report_figure_sha256=sha(r['report_figure']),
                           classification='External contextual calculation' if r['panel'] in ['1A','1B','1C'] or r['panel'].startswith('S5') else 'Own partial processing of observations or metadata',
                           limitations=r['blocker']))
    layout=json.loads((ROOT/'report/figure_layout.json').read_text())
    assert not next(x for x in layout if x['figure']=='S6')['independent_files']
    assert not json.loads((D/'velest_summary.json').read_text())['accepted_independent_result']
    paper=(ROOT/'report/report.fls').read_text();comparison=(ROOT/'report/comparison.fls').read_text()
    assert all(r['report_figure'] in paper and r['report_figure'] in comparison for r in chains)
    assert 'reference_assets' not in paper and 'quarantine/' not in paper and 'tests/results' not in paper
    assert 'reference_assets' in comparison
    for name in ['plot_continuation.py','plot_observations.py','downstream_checks.py','process_continuous.py','catalog_frequency_index.py']:
        text=(ROOT/'scripts'/name).read_text()
        assert 'science.adw9038' not in text and 'reference_assets' not in text and 'quarantine/' not in text and 'tests/results' not in text
    picks=pd.read_csv(D/'picks.csv');events=pd.read_csv(D/'initial_events.csv');assigned=pd.read_csv(D/'associations.csv')
    sources=set(picks.source);assert all(p.startswith(('inputs/waveforms/','inputs/extended/waveforms/','inputs/continuation/waveforms/')) and (ROOT/p).is_file() for p in sources)
    assert picks.probability.between(.3,1).all() and assigned.pick_index.is_unique
    assert assigned.pick_index.between(0,len(picks)-1).all()
    counts=assigned.groupby('event_index').size();assert (counts>=6).all()
    assert set(counts.index)==set(events.event_index)
    assert np.array_equal(counts.reindex(events.event_index).to_numpy(),events.num_picks.to_numpy())
    lev=pd.read_csv(D/'historical_leveling.csv');assert lev.provenance_class.value_counts().to_dict()=={'leveling survey':114,'source-provided estimate':13,'source-provided reconstruction':1}
    station=pd.read_csv(D/'station_geometry_qa.csv');assert len(station)==51 and np.isfinite(station[['x_km','y_km']]).all().all()
    requests=pd.read_csv(D/'request_ledger.csv.gz');assert (requests.loc[~requests.status.eq('downloaded'),'returned_channel_hours']==0).all()
    # Independently verify the saved weighted normal equations for each solved
    # magnitude component, without opening observations or reference-result data.
    edges=pd.read_csv(D/'magnitude_edges.csv');m=pd.read_csv(D/'magnitudes.csv').set_index('event_index');priors=pd.read_csv(D/'routine_matches.csv')
    gradient={int(i):0. for i in m.index}
    for r in edges.itertuples():
        if r.event_a not in gradient or r.event_b not in gradient:continue
        residual=float(m.loc[r.event_a,'ML']-m.loc[r.event_b,'ML']-r.delta_M)
        gradient[r.event_a]+=r.weight*residual;gradient[r.event_b]-=r.weight*residual
    for r in priors.itertuples():
        if r.event_index in gradient and np.isfinite(r.Md):gradient[r.event_index]+=float(m.loc[r.event_index,'ML']-r.Md)
    norm=max(map(abs,gradient.values()),default=0.);assert norm<1e-7,norm
    fi=pd.read_csv(D/'catalog_frequency_index.csv');fi_events=pd.read_csv(D/'catalog_frequency_index_events.csv').set_index('event_index')
    assert fi[['event_index','station']].duplicated().sum()==0 and np.isfinite(fi.FI).all()
    assert set(fi.event_index)<=set(events.event_index) and set(fi.source)<=set(pd.read_csv(D/'processed_coverage.csv').file)
    computed=fi.groupby('event_index').FI.mean().sort_index()
    assert np.allclose(computed,fi_events.loc[computed.index,'mean_FI'],rtol=1e-12,atol=1e-12)
    assert not fi.reviewed.any() and json.loads((D/'catalog_frequency_index.json').read_text())['confirmed_hybrids']==0
    result=dict(passed=True,partial_panel_chains=chains,picks_checked=len(picks),raw_pick_source_files=len(sources),provisional_events=len(events),
                magnitude_normal_equation_max_abs_residual=norm,frequency_index_station_measurements=len(fi),frequency_index_event_means_verified=len(fi_events),published_reference_images_only_in_comparison=True,
                no_test_fixture_or_quarantined_result_in_inspected_panel_chains=True,
                association_software_test=json.loads((ROOT/'tests/results/association_validation.json').read_text()),
                scope='Explicit current file graph and listed invariants only. Does not prove absence of unexamined/hidden inputs or establish scientific accuracy of provisional events. S6 is excluded, and no panel is fully reproduced.')
    (D/'provenance_validation.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: current partial-panel chains, provenance boundaries and saved numerical consistency.')

if __name__=='__main__':main()
