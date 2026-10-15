"""Compare own associations by observed phase identity, never by integer event ID."""
import argparse,hashlib,json
from pathlib import Path
import pandas as pd
from obspy import UTCDateTime
ROOT=Path(__file__).resolve().parents[1]
def fingerprints(directory):
    picks=pd.read_csv(directory/'picks.csv');a=pd.read_csv(directory/'associations.csv')
    q=a.merge(picks,left_on='pick_index',right_index=True)
    return {hashlib.sha256(json.dumps(sorted(zip(g.trace_id,g.phase,g.time))).encode()).hexdigest():int(e) for e,g in q.groupby('event_index')}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--observations',required=True);a=ap.parse_args();D=ROOT/a.observations;prior=ROOT/'data/eida_continuation'
    old=fingerprints(prior);new=fingerprints(D);common=set(old)&set(new)
    result=dict(prior=str(prior.relative_to(ROOT)),current=str(D.relative_to(ROOT)),identical_phase_sets=len(common),new_or_changed_phase_sets=len(new)-len(common),prior_sets_no_longer_identical=len(old)-len(common),identity='Sorted own station identifier, phase and absolute arrival time; IDs and locations do not establish equivalence.',event_id_map=[dict(previous_event=old[k],current_event=new[k],arrival_set_sha256=k) for k in sorted(common)])
    (D/'cohort_comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    a=float(UTCDateTime('2024-12-01'));b=a+21600;rows=[]
    for r in json.loads((D/'processed_coverage_union.json').read_text()):
        hours=sum(max(0,min(y,b)-max(x,a)) for x,y in r['intervals'])/3600
        if hours:rows.append(dict(channel=r['channel'],processed_hours=hours))
    pd.DataFrame(rows).to_csv(D/'december_window_coverage.csv',index=False)
    av=pd.read_csv(ROOT/'data/availability_extension/advertised_intervals.csv');window=av[(av.start<b)&(av.end>a)]
    stations=lambda values:sorted({'.'.join(c.split('.')[:2]) for c in values})
    receipt=dict(window=['2024-12-01T00:00:00Z','2024-12-01T06:00:00Z'],processed_channels=len(rows),processed_station_count=len(stations(r['channel'] for r in rows)),processed_channel_hours=sum(r['processed_hours'] for r in rows),advertised_stations=stations(window.channel),stations_without_advertised_records_in_window=sorted(set(stations(av.channel))-set(stations(window.channel))),source='Original public continuous observations; calendar/metadata-selected window, not earthquake-catalog selection.')
    (D/'december_window_coverage.json').write_text(json.dumps(receipt,indent=2)+'\n')
    q=pd.read_csv(D/'selection/input_quality.csv');q=q[~q.event_index.isin([new[k] for k in common])]
    q.to_csv(D/'new_association_quality.csv',index=False)
    quality=dict(new_associations=len(q),causal=int(q.causal.sum()),calibration_eligible=int(q.calibration.sum()),criteria_failed_counts=dict(fewer_than_four_P=int((q.P<4).sum()),fewer_than_two_S=int((q.S<2).sum()),ten_or_fewer_total_phases=int((q.picks<=10).sum()),azimuth_gap_at_least_180=int((q.gap_deg>=180).sum()),noncausal=int((~q.causal).sum())),note='Criteria overlap. No threshold relaxed; these are project-selected quality screens, not manual review.')
    (D/'new_association_quality.json').write_text(json.dumps(quality,indent=2)+'\n')
    print({k:v for k,v in result.items() if k!='event_id_map'})
if __name__=='__main__':main()
