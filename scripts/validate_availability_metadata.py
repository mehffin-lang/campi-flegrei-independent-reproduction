"""Response epoch and sampling checks on actual stored trace intervals."""
import json
import numpy as np,pandas as pd
from obspy import UTCDateTime as U
import availability_extension as a
def main():
    cov=pd.read_csv(a.D/'coverage_intervals.csv');meta=pd.read_csv(a.D/'response_epochs.csv',keep_default_na=False);rows=[]
    for ch,g in cov.groupby('channel'):
        net,sta,loc,channel=ch.split('.');q=meta[(meta.network==net)&(meta.station==sta)&(meta.location==loc)&(meta.channel==channel)]
        spans=[]
        for r in q.itertuples():
            x=max(a.A,float(U(r.start)));y=min(a.B,float(U(r.end))) if r.end not in ['','None'] else a.B
            if r.response:spans.append((x,y))
        gaps=a.subtract(zip(g.start,g.end),spans)
        rows.append(dict(channel=ch,observed_hours=a.seconds(zip(g.start,g.end))/3600,response_gap_hours=a.seconds(gaps)/3600,metadata_epochs=len(q),coordinate_valid=bool(len(q) and q.latitude.between(-90,90).all() and q.longitude.between(-180,180).all()),sample_rates=','.join(map(str,sorted(q.sample_rate.unique())))))
    pd.DataFrame(rows).to_csv(a.D/'metadata_coverage_qa.csv',index=False)
    group=meta.groupby(['network','station'])[['latitude','longitude','elevation_m','sample_rate']].agg(lambda v:v.max()-v.min());group.to_csv(a.D/'station_metadata_epoch_ranges.csv')
    # Baseline and completed receipts carry observed sample rates separately.
    raw=pd.read_csv(a.D/'baseline_trace_intervals.csv');rates={ch:set(g.sample_rate) for ch,g in raw.groupby('channel')}
    conn=a.database()
    for r in conn.execute("select receipt from requests where status='downloaded'"):
        for s in json.loads(r[0])['segments']:rates.setdefault(s['channel'],set()).add(s['sample_rate'])
    conn.close();mismatch=[]
    for ch,fs in rates.items():
        net,sta,loc,c=ch.split('.');documented=set(meta.loc[(meta.network==net)&(meta.station==sta)&(meta.location==loc)&(meta.channel==c),'sample_rate']);unknown=fs-documented
        if unknown:mismatch.append(dict(channel=ch,observed=sorted(fs),metadata=sorted(documented)))
    a.dump(a.D/'metadata_validation.json',dict(channels_checked=len(rows),response_gap_channels=[r for r in rows if r['response_gap_hours']>1e-6],invalid_coordinates=[r for r in rows if not r['coordinate_valid']],sample_rate_mismatches=mismatch,limitations='Checks epoch support and reported sample rates, not response deconvolution accuracy or pole/zero calibration. Static station coordinates in existing inversion differ slightly between some epochs; range table retains this approximation.'))
if __name__=='__main__':main()
