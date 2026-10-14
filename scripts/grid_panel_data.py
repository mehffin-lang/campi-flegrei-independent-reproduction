"""Numerical panel selections and CPOZ measurements from own relocated events."""
from pathlib import Path
import json,hashlib,os
import numpy as np
import pandas as pd
from obspy import read,UTCDateTime
from pyproj import Transformer
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/os.environ.get('CF_GRID_BASE','data/grid_calibration')/'merged4';OUT=BASE/'panels';D=ROOT/os.environ.get('CF_OBSERVATIONS','data/calibration_followup/expanded')
PROJ=Transformer.from_crs('EPSG:4326','+proj=aeqd +lat_0=40.82 +lon_0=14.14 +datum=WGS84 +units=km',always_xy=True)

def main():
    OUT.mkdir(exist_ok=True)
    e=pd.read_csv(BASE/'uncertainty/relocated_events.csv');vel=pd.read_csv(BASE/'filtered_events.csv')
    magnitudes=pd.read_csv(BASE/'magnitude/magnitudes.csv')
    for f,df in [('relocated.csv',e),('velest.csv',vel)]:
        df['x_km'],df['y_km']=PROJ.transform(df.longitude.to_numpy(),df.latitude.to_numpy())
        df=df.merge(magnitudes[['event_index','ML']],on='event_index',how='left');df.to_csv(OUT/f,index=False)
    e=pd.read_csv(OUT/'relocated.csv');t=pd.to_datetime(e.time,utc=True)
    # Spatial masks are display/analysis alternatives, not a digitized published
    # polygon or author-derived event classification. No empirical depth bands
    # from Tan are used to impose a ring or select apparent agreement.
    e['sector']=np.where(e.y_km>=1.5,'North',np.where(e.x_km>=1.,'East',np.where((e.x_km<=-2.)|(e.y_km<=-1.),'Southwest','Other')))
    e.to_csv(OUT/'sectors.csv',index=False)
    bins=pd.date_range('2022-01-21','2025-03-28',freq='7D',tz='UTC')
    weekly=[];cover=pd.read_csv(D/'processed_coverage.csv');routine=pd.read_csv('data/continuation/figure_S5.csv');rt=pd.to_datetime(routine.time,utc=True,format='ISO8601')
    for a,b in zip(bins[:-1],bins[1:]):
        mask=(t>=a)&(t<b);r=(rt>=a)&(rt<b)
        selected=cover[(cover.start<b.timestamp())&(cover.end>a.timestamp())]
        weekly.append(dict(start=a.isoformat(),end=b.isoformat(),independent_events=int(mask.sum()),context_routine_events=int(r.sum()),recorded_station_names=selected.channel.str.split('.').str[1].nunique(),
              other=int((mask&(e.sector=='Other')).sum()),geographic_sectors=int((mask&(e.sector!='Other')).sum())))
    pd.DataFrame(weekly).to_csv(OUT/'weekly_counts.csv',index=False)
    groups=[]
    windows=[('swarm-1','2022-03-01','2022-04-01'),('swarm-2','2023-09-25','2023-10-03'),('swarm-3','2024-05-18','2024-05-25'),('swarm-4','2025-02-12','2025-02-19')]
    for name,a,b in windows:
        # Titles specify calendar dates only. Inclusive end day is an explicit
        # convention, not inferred from the published event distribution.
        x=e[(t>=pd.Timestamp(a,tz='UTC'))&(t<pd.Timestamp(b,tz='UTC')+pd.Timedelta(days=1))]
        x.to_csv(OUT/(name+'.csv'),index=False);groups.append(dict(panel='S11/'+name,events=len(x),start=a,end_inclusive=b))
    for year in range(2022,2026):
        x=e[t.dt.year==year];x.to_csv(OUT/f'year{year}.csv',index=False);groups.append(dict(panel=f'S10/{year}',events=len(x)))
    # Supplement p. S8 removes sums below 100; retain equality at 100.
    high=e[(e.ncc_p+e.ncc_s)>=100];high.to_csv(OUT/'best_located.csv',index=False)
    # CPOZ independently picked arrivals, now joined to the same-cohort relocated
    # IDs; old 1003-event gathers are not eligible for this join.
    picks=pd.read_csv(BASE/'tomodd/retained_picks.csv');p=picks[(picks.trace_id.str.split('.').str[1]=='CPOZ')&(picks.phase=='P')].merge(e,on='event_index',suffixes=('_pick','_event'))
    rows=[];arrays={};errors=[]
    for source,g in p.groupby('source'):
        stream=read(str(ROOT/source)).select(station='CPOZ').merge(method=0).split()
        for r in g.itertuples():
            start=UTCDateTime(r.time_pick)
            for channel in ['HHZ','HHN']:
                try:
                    st=stream.select(channel=channel).slice(start-16,start+22).copy()
                    if len(st)!=1:raise ValueError('No single gap-free component')
                    tr=st[0];fs=tr.stats.sampling_rate
                    if tr.stats.starttime>start-1 or tr.stats.endtime<start+7-1/fs:raise ValueError('Incomplete eight-second window')
                    tr.detrend('demean');tr.filter('highpass',freq=4,corners=4,zerophase=False);tr.trim(start-1,start+7-1/fs)
                    if len(tr)!=round(8*fs) or np.max(abs(tr.data))==0:raise ValueError('Empty/incomplete window')
                    key=f'e{r.event_index}_{channel}';arrays[key]=np.vstack([tr.times()+float(tr.stats.starttime-start),tr.data/np.max(abs(tr.data))])
                    rows.append(dict(event_index=r.event_index,channel=channel,array_key=key,source=source,p_time=r.time_pick,sector=r.sector,x_km=r.x_km,y_km=r.y_km,depth_km=r.depth_km,sample_rate_hz=fs,normalizer_counts=float(np.max(abs(tr.data)))))
                except Exception as exc:errors.append(dict(event_index=r.event_index,channel=channel,error=repr(exc)))
    pd.DataFrame(rows).to_csv(OUT/'cpoz_index.csv',index=False);np.savez_compressed(OUT/'cpoz_gathers.npz',**arrays)
    sp=[]
    for (eid,sta),g in picks[picks.event_index.isin(e.event_index)].groupby(['event_index','trace_id']):
        if set(g.phase)=={'P','S'}:
            pp=g[g.phase=='P'].iloc[0];ss=g[g.phase=='S'].iloc[0];sp.append(dict(event_index=eid,station=sta,sp_s=float(UTCDateTime(ss.time)-UTCDateTime(pp.time)),p_source=pp.source,s_source=ss.source))
    sp=pd.DataFrame(sp).merge(e[['event_index','sector','depth_km']],on='event_index');sp.to_csv(OUT/'sp_measurements.csv',index=False)
    summary=dict(events=len(e),velest_events=len(vel),magnitudes=len(magnitudes),above_5km=int((e.depth_km>5).sum()),above_5km_velest=int((vel.depth_km>5).sum()),best_located_events=len(high),groups=groups,cpoz_events=len(p),cpoz_traces=len(rows),cpoz_sectors=pd.DataFrame(rows).groupby('sector').size().to_dict(),errors=errors,
        sector_masks='Explicit alternative: North y>=1.5 km; remaining East x>=1 km; remaining Southwest x<=-2 or y<=-1 km; remainder Other. Local WGS84 AEQD centered 40.82N 14.14E. No depth filter. These are not the unpublished original masks.',
        counts='Seven-day bins anchored 21 January 2022; sparse observed-window counts, not exposure-corrected rates. Routine counts are separate context and never seed events. Unobserved weeks are not empirical zeros.',
        swarm_dates='Written panel-title date ranges from S11; only selection metadata read, never plotted coordinates, magnitudes or count values. End day inclusive assumed.',
        input_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [BASE/'uncertainty/relocated_events.csv',BASE/'filtered_events.csv',BASE/'magnitude/magnitudes.csv',BASE/'tomodd/retained_picks.csv',D/'processed_coverage.csv',ROOT/'data/continuation/figure_S5.csv']})
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
