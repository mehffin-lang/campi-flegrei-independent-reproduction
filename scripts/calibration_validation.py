"""Additional convergence, residual, and metadata checks on observed events."""
import json,re
import numpy as np
import pandas as pd
from obspy import read_inventory,UTCDateTime
from pyproj import Geod
import calibration_chain as c


def main():
    ids=pd.read_csv(c.OUT/'calibration_selection.csv').event_index.tolist()
    previous=pd.read_csv(c.OUT/'calibration_convergence_locations.csv');work=c.WORK/'calibration_convergence';rows=[]
    for i in range(2,6):
        old=c.v.model_table(work/'velout.mod')
        nw,loc,r=c.run(f'convergence_extra{i}',(work/'velout.mod').read_text(),c.normalize_stations((work/'output.sta').read_text()),(work/'output.cnv').read_text(),ids,corrections=True)
        r['change']=c.compare(previous,loc)
        r['max_velocity_change_km_s']=float(np.max(abs(old[['Vp_km_s','Vs_km_s']].to_numpy()-c.v.model_table(nw/'velout.mod')[['Vp_km_s','Vs_km_s']].to_numpy())))
        rows.append(r);previous=loc;work=nw
    (c.OUT/'convergence_path.json').write_text(json.dumps(rows,indent=2)+'\n')
    residual_rows=[];checks=[]
    for name in ['heldout_starting','heldout_fitted','calibration_64_round2','whole_catalog_pass5']:
        work=c.WORK/name
        locations=pd.read_csv(c.OUT/(name+'_locations.csv'))
        residual=np.loadtxt(work/'residuals.txt',ndmin=2)[:,1];cursor=0
        blocks=re.split(r'\n\s*\n',(work/'output.cnv').read_text().strip())
        for e,block in zip(locations.itertuples(),blocks):
            tokens=[line[i:i+12] for line in block.splitlines()[1:] for i in range(0,len(line.rstrip()),12)]
            rr=residual[cursor:cursor+len(tokens)];cursor+=len(tokens)
            weight=np.array([1. if token[4]=='P' else .5 for token in tokens]);weight*=len(tokens)/weight.sum()
            computed=float(np.std(rr*weight,ddof=1))
            checks.append(dict(run=name,event_index=e.event_index,reported_rms_s=e.rms_s,recomputed_rms_s=computed,absolute_difference_s=abs(e.rms_s-computed)))
            residual_rows.extend(dict(run=name,event_index=e.event_index,alias=tok[:4],phase=tok[4],residual_s=float(r)) for tok,r in zip(tokens,rr))
        assert cursor==len(residual)
    pd.DataFrame(residual_rows).to_csv(c.OUT/'phase_residuals.csv',index=False)
    check=pd.DataFrame(checks);check.to_csv(c.OUT/'rms_recalculation.csv',index=False)
    # Check the actual coordinate/response epochs for retained arrival times.
    picks=pd.read_csv(c.OUT/'relocation/retained_picks.csv');static=pd.read_csv(c.OUT/'station_aliases.csv').set_index('id')
    inventory={net:read_inventory(str(c.ROOT/f'inputs/continuation/{net}_responses.xml')) for net in ['IV','2I']}
    geod=Geod(ellps='WGS84');epochs=[];missing_groups=[];groups=0
    for (ident,day),group in picks.groupby(['trace_id',picks.time.str[:10]]):
        groups+=1;prior=len(epochs)
        net,sta,loc=ident.split('.');time=UTCDateTime(group.time.iloc[0]);selected=inventory[net].select(station=sta,location=loc,time=time)
        for network in selected:
            for station in network:
                for ch in station:
                    _,_,distance=geod.inv(float(static.loc[ident,'longitude']),float(static.loc[ident,'latitude']),ch.longitude,ch.latitude)
                    epochs.append(dict(trace_id=ident,day=day,channel=ch.code,latitude=ch.latitude,longitude=ch.longitude,elevation_m=ch.elevation,depth_m=ch.depth,
                        epoch_start=str(ch.start_date),epoch_end=str(ch.end_date),static_offset_m=distance,
                        response_complete=bool(ch.response and ch.response.instrument_sensitivity and ch.response.response_stages)))
        if len(epochs)==prior:missing_groups.append(dict(trace_id=ident,day=day))
    epoch=pd.DataFrame(epochs);epoch.to_csv(c.OUT/'retained_pick_metadata_epochs.csv',index=False)
    summary=dict(rms_formula='Sample standard deviation of residual times normalized VELEST weights, not unweighted RMS; weight S/P=0.5 and sum(weights)=n.',
        maximum_rms_serialization_difference_s=float(check.absolute_difference_s.max()),
        rms_agrees_with_printed_precision=bool((check.absolute_difference_s<=.006).all()),
        station_epoch_rows=len(epoch),max_static_coordinate_offset_m=float(epoch.static_offset_m.max()),all_listed_responses_complete=bool(epoch.response_complete.all()),
        station_day_groups=groups,missing_station_day_groups=missing_groups,epoch_sampling='First retained arrival per station and UTC day; complete interval intersections audited separately.',
        interpretation='Precision agreement is established, but continued iterations do not converge to stable locations. Fitted model remains exploratory; residual and covariance reductions do not establish accuracy.')
    (c.OUT/'validation.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
