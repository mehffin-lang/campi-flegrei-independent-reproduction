"""Verify explicit provenance, numerical gates and style receipts; not absolute accuracy."""
from pathlib import Path
import json,hashlib,zipfile
import numpy as np
import pandas as pd
from obspy import UTCDateTime
from pyproj import Geod
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/grid_calibration';O=D/'merged4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
    assert sha(D/'reference_grid.original')==read(D/'source_access.json')['sha256']
    inv=read(D/'input_inventory.json')
    for p,h in inv['files'].items():assert sha(ROOT/p)==h,p
    s=read(O/'summary.json');v=read(O/'validation.json');t=read(O/'tomodd/summary.json')
    for p,h in v['sources'].items():assert sha(ROOT/p)==h,p
    for p,h in read(O/'tomodd/measurement.json')['files'].items():assert sha(ROOT/p)==h,p
    f=pd.read_csv(O/'filtered_events.csv');assert len(f)==s['paper_filter_passing']
    assert ((f.num_picks>=6)&(f.rms_s<=.25)&(f.azimuthal_gap_deg<=300)).all()
    retained=pd.read_csv(O/'tomodd/retained_picks.csv');original=pd.read_csv(ROOT/'data/calibration_followup/expanded/picks.csv').loc[retained.pick_index].reset_index(drop=True)
    assert original.time.equals(retained.time) and original.source.equals(retained.source)
    assert retained.travel_s.gt(0).all() and retained.cnv_drift_s.abs().max()<=.06
    assert not ((original.phase=='S')&original.trace_id.str.split('.').str[1].isin(['CASE','CFB1','CFB3'])).any()
    relocation_checks=[];stations=pd.read_csv(O/'station_aliases.csv').set_index('alias')
    for n in [1,2]:
        loc=pd.read_csv(O/f'tomodd/round{n}_locations.csv').set_index('event_index');res=pd.read_csv(O/f'tomodd/round{n}_residuals.csv');res=res[res.weight>0]
        assert set(loc.index+1)<=set(res.event_a)|set(res.event_b)
        for eid,e in loc.iterrows():
            sta=stations.loc[res.loc[(res.event_a==eid+1)|(res.event_b==eid+1),'alias'].unique()]
            az,_,_=Geod(ellps='WGS84').inv(np.full(len(sta),e.longitude),np.full(len(sta),e.latitude),sta.longitude,sta.latitude);aa=np.sort(np.mod(az,360));gap=float(np.diff(np.r_[aa,aa[0]+360]).max())
            assert np.isclose(gap,e.gap_deg)
        picks=retained[retained.event_index.isin(loc.index)];travel=[UTCDateTime(r.time)-UTCDateTime(loc.loc[r.event_index,'time']) for r in picks.itertuples()]
        assert min(travel)>0
        relocation_checks.append(dict(round=n,output_events=len(loc),residual_events=len(set(res.event_a)|set(res.event_b)),gap_passes=int(loc.gap_deg.le(300).sum()),minimum_retained_travel_s=float(min(travel))))
    plotted=set()
    for r in read(D/'style/plot_inventory.json'):
        for p,h in {**r['inputs'],**r['outputs']}.items():assert sha(ROOT/p)==h,p
        plotted.update(r['outputs'])
        assert not any('reference_assets' in p or 'quarantine/' in p or 'tests/' in p for p in r['inputs'])
    figures={str(p.relative_to(ROOT)) for p in (ROOT/'figures').glob('*') if p.suffix in ['.pdf','.png']}
    assert figures==plotted,figures.symmetric_difference(plotted)
    for panel in ['1A','S5']:
        style=read(ROOT/'data/continuation/routine_plot_style.json')[panel];x=pd.read_csv(ROOT/style['input'])
        assert sha(ROOT/style['input'])==style['sha256'] and style['color_limits_km']==[0.,5.] and style['clip'] is False
        assert int(x.depth_km.gt(5).sum())==style['over_count'] and int(x.depth_km.lt(0).sum())==style['under_count']
    for r in read(D/'style/spectral_scales.json'):assert r['limits_dB']==[-80,0] and not r['clipped']
    panels=read(ROOT/'docs/panel_record.json');assert len(panels)==63
    assert all(r['plot_command']=='.venv/bin/python scripts/publication_plots.py' for r in panels if r['status']=='partially reproduced')
    with zipfile.ZipFile(D/'run_records.zip') as z:
        for p,h in read(D/'run_records.json').items():assert hashlib.sha256(z.read(p)).hexdigest()==h,p
    result=dict(passed=True,grid_original_sha256=sha(D/'reference_grid.original'),usable_events=s['whole_catalog_events'],calibration_candidates=s['calibration_events'],filter_passing=len(f),retained_own_picks=len(retained),all_current_figure_files=len(plotted),figure_groups=len(read(D/'style/plot_inventory.json')),publication_panel_views=len(panels),scientific_catalog_accepted=False,tomodd_execution_status=t['status'],limitations='Checks explicit file identities, own-pick handoffs, numerical filters and display scales; not absolute event/location accuracy, manual phase validation or proof about unexamined inputs.')
    result['relocation_checks']=relocation_checks
    (D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
