"""Raw/response-corrected zooms for unresolved first arrivals; no automatic picks."""
from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from obspy import read,read_inventory,UTCDateTime
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/mechanism_eida'
SELECTION={649:['CPIS','CQUE','CRUS'],100331:['CFB1'],100946:['CFB1'],101038:['CFB1','CBAG'],101400:['CFB1','CBAG','COLB'],101760:['CAAM','COLB'],359:['CAAM','CPOZ'],373:['CPOZ'],815:['CPOZ']}
def main():
    m=pd.read_csv(D/'measurements.csv');e=pd.read_csv(D/'candidate_locations.csv').set_index('event_index')
    inv=read_inventory(str(ROOT/'inputs/continuation/IV_responses.xml'));arrays={};rows=[]
    for eid,stations in SELECTION.items():
        for station in stations:
            r=m[(m.event_id==eid)&(m.station==station)].iloc[0];t=UTCDateTime(e.loc[eid].time)
            stream=read(str(ROOT/r.source),starttime=t-10,endtime=t+15).merge(method=0).split().select(network=r.network,station=station,component='Z');assert len(stream)==1
            tr=stream[0];meta=inv.select(network=r.network,station=station,channel=tr.stats.channel,time=t)[0][0][0];assert abs(meta.dip+90)<1
            raw=tr.copy().detrend('demean');vel=tr.copy().detrend('demean').taper(.03);vel.remove_response(inventory=inv,output='VEL',pre_filt=[.1,.2,35,45],water_level=60)
            start,end=(-1.,1.5) if eid==101760 else (.5,3.5) if eid!=649 else (1.,4.)
            key=f'e{eid}_{station}';a=raw.trim(t+start,t+end);b=vel.trim(t+start,t+end);arrays[key]=np.vstack([a.times()+float(a.stats.starttime-t),a.data,b.data])
            rows.append(dict(key=key,event_id=eid,station=station,source=r.source,source_sha256=hashlib.sha256((ROOT/r.source).read_bytes()).hexdigest(),origin_time=str(t),start_s=start,end_s=end))
    for page in range((len(rows)+3)//4):
        subset=rows[4*page:4*(page+1)];fig,axes=plt.subplots(len(subset),2,figsize=(13,2.6*len(subset)),squeeze=False,layout='constrained')
        for r,aa in zip(subset,axes):
            a=arrays[r['key']]
            for ax,y,label in zip(aa,a[1:],['Raw counts, mean removed','Response-corrected velocity (m/s)']):
                ax.plot(a[0],y,c='black',lw=.65);ax.set(xlim=(r['start_s'],r['end_s']),xlabel='Seconds from own provisional origin',ylabel=label,title=f"{r['event_id']} {r['station']} origin {r['origin_time']}");ax.grid(alpha=.25)
        fig.savefig(D/f'review/additional_onsets_{page+1}.png',dpi=140);plt.close(fig)
    pd.DataFrame(rows).to_csv(D/'additional_onset_windows.csv',index=False);np.savez_compressed(D/'additional_onset_windows.npz',**arrays)
    print('Rendered',len(rows),'original observation windows; no arrival or polarity inferred by this script.')
if __name__=='__main__':main()
