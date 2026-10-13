"""Check current observed-data chains and preserve scientific rejection flags."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/calibration_followup'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

class DepthCells(HTMLParser):
    """Read only literal depth cells; do not execute or infer HTML content."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depths={};self.active=None;self.active_tag=None;self.parts=[]
    def handle_starttag(self,tag,attrs):
        ident=dict(attrs).get('id','')
        if ident.startswith('dep_'):
            assert self.active is None, 'Nested depth fields are not supported'
            self.active=ident[4:];self.active_tag=tag;self.parts=[]
    def handle_data(self,data):
        if self.active is not None:self.parts.append(data)
    def handle_endtag(self,tag):
        if tag==self.active_tag and self.active is not None:
            self.depths[self.active]=''.join(self.parts).strip();self.active=None

def main():
    s=json.loads((D/'summary.json').read_text());r=json.loads((D/'relocation/summary.json').read_text())
    for p,h in s['inputs'].items():assert sha(ROOT/p)==h,p
    for p,h in r['input_sha256'].items():assert sha(ROOT/p)==h,p
    measurement=json.loads((D/'relocation/measurement.json').read_text())
    for p,h in measurement['files'].items():assert sha(ROOT/p)==h,p
    selected=pd.read_csv(D/'filtered_events.csv');assert len(selected)==s['paper_filter_passing']
    assert ((selected.num_picks>=6)&(selected.rms_s<=.25)&(selected.azimuthal_gap_deg<=300)).all()
    kept=pd.read_csv(D/'relocation/retained_picks.csv');picks=pd.read_csv(ROOT/'data/continuation/picks.csv')
    lookup=picks.loc[kept.pick_index].reset_index(drop=True)
    assert lookup.time.equals(kept.time) and lookup.source.equals(kept.source)
    assert kept.source.str.startswith(('inputs/waveforms/','inputs/extended/waveforms/','inputs/continuation/waveforms/')).all()
    assert kept.travel_s.gt(0).all() and kept.cnv_drift_s.abs().max()<.06
    expanded=D/'expanded';summary=json.loads((expanded/'analysis_summary.json').read_text())
    ep=pd.read_csv(expanded/'picks.csv');ea=pd.read_csv(expanded/'associations.csv');ev=pd.read_csv(expanded/'initial_events.csv')
    assert len(ep)==summary['picks'] and len(ev)==summary['events'] and len(ea)==summary['assigned_picks']
    assert ea.pick_index.is_unique and ea.pick_index.between(0,len(ep)-1).all()
    assert (ea.groupby('event_index').size()>=6).all()
    assert ep.probability.between(.3,1).all()
    assert not ((ep.phase=='S')&ep.trace_id.str.split('.').str[1].isin(['CASE','CFB1','CFB3'])).any()
    assert set(ep.source)<=set(pd.read_csv(expanded/'processed_coverage.csv').file)
    template_sources={str(p.relative_to(ROOT)) for label in ['E1','E2','E3'] for p in (ROOT/'inputs/waveforms').glob(label+'_*.mseed')}
    assert set(ep.source).isdisjoint(template_sources)
    assert 'inputs/resumption/S4_CSOB_20240520.mseed' not in set(ep.source)
    receipts=json.loads((expanded/'processed_input_receipts.json').read_text())
    assert {r['file'] for r in receipts}==set(pd.read_csv(expanded/'processed_coverage.csv').file)
    for item in json.loads((expanded/'input_jobs.json').read_text()):assert sha(ROOT/item['file'])==item['sha256']
    audit=json.loads((expanded/'coverage_audit.json').read_text())
    assert np.isclose(audit['response_covered_channel_hours']+audit['missing_response_channel_hours'],summary['processed_channel_hours'])
    # The style change must not modify empirical numerical tables.
    style=json.loads((ROOT/'data/continuation/routine_plot_style.json').read_text())
    for key in ['1A','S5']:
        entry=style[key];assert sha(ROOT/entry['input'])==entry['sha256']
        values=pd.read_csv(ROOT/entry['input']);assert len(values)==entry['events']
        lo,hi=entry['color_limits_km'];assert [lo,hi]==[0.,5.] and entry['clip'] is False
        assert int(values.depth_km.lt(lo).sum())==entry['under_count']
        assert int(values.depth_km.gt(hi).sum())==entry['over_count']
    routine=pd.read_csv(ROOT/'data/continuation/figure_S5.csv',dtype={'id':str});source_hashes={}
    for source,group in routine.groupby('source'):
        parser=DepthCells();parser.feed((ROOT/source).read_text());parser.close()
        depths=parser.depths
        assert np.allclose([float(depths[str(r.id)]) for r in group.itertuples()],group.depth_km,rtol=0,atol=1e-12)
        source_hashes[source]=sha(ROOT/source)
    precision=dict(events=len(routine),unique_depths=int(routine.depth_km.nunique()),
        fraction_on_0_1_km_grid=float(np.mean(np.isclose(routine.depth_km*10,np.round(routine.depth_km*10)))),
        raw_HTML_values_match=True,source_sha256=source_hashes,
        meaning='Precision of the permitted public routine-catalog snapshot, not depth accuracy; values are neither jittered nor smoothed to resemble the publication.')
    (D/'routine_depth_precision.json').write_text(json.dumps(precision,indent=2)+'\n')
    for name in ['calibration_chain.py','relocation_followup.py','routine_plot_style.py','plot_calibration_followup.py']:
        source=(ROOT/'scripts'/name).read_text()
        assert all(token not in source for token in ['read_csv(\'science.adw9038','reference_assets/','quarantine/','background_3d_vmod'])
    assert not s['accepted_scientific_calibration'] and not r['accepted_scientific_result']
    files=[p for p in D.rglob('*') if p.is_file() and p.name not in ['verification.json','rebuild_status.json','processing_checkpoint.json']]
    output=dict(passed=True,scope='Explicit saved input/output identities, response coverage, pick exclusions, numerical filters and plotting bounds; not a proof of absolute accuracy or absence of unexamined inputs.',
        calibration_accepted=False,TomoDD_completed=False,partial_or_failed_SVD=True,
        expanded_events=len(ev),retained_own_picks=len(kept),style_input_values_unchanged=True,
        files={str(p.relative_to(ROOT)):sha(p) for p in files})
    (D/'verification.json').write_text(json.dumps(output,indent=2)+'\n')
    print('PASS: explicit observed-data chains and checks; scientific calibration remains rejected.')

if __name__=='__main__':main()
