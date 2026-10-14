"""Run generic SKHASH on independently measured, AI-reviewed observations."""
from pathlib import Path
import json,shutil,subprocess,hashlib,os
import pandas as pd,numpy as np
ROOT=Path(__file__).resolve().parents[1];D=ROOT/os.environ.get('CF_MECH_OUT','data/mechanism_followup')
DECISIONS=ROOT/os.environ.get('CF_MECH_DECISIONS','config/mechanism_visual_decisions.json')
def main():
    decision=json.loads(DECISIONS.read_text());f=pd.read_csv(D/'measurements.csv')
    f['reviewer']=decision['reviewer'];f['human_reviewed']=False;f['polarity_accepted']=False;f['sp_accepted']=False;f['p_polarity']=np.nan;f['review_reason']='';f['sp_review_reason']=''
    for i,r in f.iterrows():
        eid=str(r.event_id);sign=decision['accepted_polarities'][eid].get(r.station)
        f.loc[i,'review_reason']=decision['polarity_notes'].get(eid+'_'+r.station,'First coherent lobe has the same sign in raw upward counts and corrected velocity.' if sign else decision['unpicked_rejection'] if pd.isna(r.p_time) else decision['general_rejection'])
        if sign:
            assert pd.notna(r.p_time)
            f.loc[i,'polarity_accepted']=True;f.loc[i,'p_polarity']=sign*(.25 if eid+'_'+r.station=='649_CBAC' else .5)
        accepted=r.station in decision['accepted_sp_windows'][eid] and r.sp_usable==True
        f.loc[i,'sp_accepted']=accepted;f.loc[i,'sp_review_reason']=decision['sp_caution'] if accepted else str(r.get('sp_reason',''))+'; arrival/packet not accepted on visual review'
    f.to_csv(D/'review_decisions.csv',index=False)
    f['horz_uncert_km']=.655;f['vert_uncert_km']=1.04
    if os.environ.get('CF_MECH_MODEL'):
        base=(ROOT/os.environ['CF_MECH_MODEL']).parent
        regional=json.loads((base/'summary.json').read_text())['starting_model_dependence'];precision=json.loads((base/'validation.json').read_text())['precision_difference']
        f['horz_uncert_km']=max(.655,regional['max_horizontal_m']/1000,precision['max_horizontal_m']/1000)
        f['vert_uncert_km']=max(1.04,regional['max_depth_km'],precision['max_depth_km'])
    # Do not pass our display azimuth column without takeoff angles. SKHASH
    # interprets supplied angle fields as complete ray geometry and bypasses
    # StationXML-derived station coordinates, producing NaNs for ratio-only rows.
    pc=['event_id','network','station','location','channel','p_polarity','origin_latitude','origin_longitude','origin_depth_km','horz_uncert_km','vert_uncert_km','source','p_time','reviewer','human_reviewed','review_reason']
    f.loc[f.polarity_accepted,pc].to_csv(D/'polarities.csv',index=False)
    cols=['event_id','network','station','location','channel','origin_latitude','origin_longitude','origin_depth_km','horz_uncert_km','vert_uncert_km','amp_p','amp_s','noise_p','noise_s','source','p_time','s_time']
    f.loc[f.sp_accepted,cols].to_csv(D/'sp_ratios.csv',index=False)
    if os.environ.get('CF_MECH_MODEL'):
        import run_velest as v
        model=v.model_table(ROOT/os.environ['CF_MECH_MODEL']);z=[];vp=[]
        for i,r in model.iterrows():
            z.append(max(0.,r.layer_top_km));vp.append(r.Vp_km_s)
            if i+1<len(model):z.append(model.layer_top_km.iloc[i+1]-.0001);vp.append(r.Vp_km_s)
        z.append(20.);vp.append(vp[-1]);np.savetxt(D/'velocity.csv',np.c_[z,vp],delimiter=',',header='depth_km,velocity_km_s')
    else:shutil.copyfile(ROOT/'data/coverage_extension/calibration/merged4/focal/velocity.csv',D/'velocity.csv')
    control={'input_format':'skhash','fpfile':str(D/'polarities.csv'),'ampfile':str(D/'sp_ratios.csv'),'stfile':str(D/'stations.csv'),'outfile1':str(D/'solutions.csv'),'outfile2':str(D/'acceptable_planes.csv'),'outfile_pol_info':str(D/'used_measurements.csv'),'vmodel_paths':str(D/'velocity.csv'),'npolmin':8,'max_agap':90,'max_pgap':60,'nmc':30,'look_dep':'0 10 1','look_del':'0 120 1','nd0':11,'nx0':121,'num_cpus':1,'overwrite_output_file':'True'}
    (D/'control.txt').write_text('\n'.join('$'+k+'\n'+str(v) for k,v in control.items())+'\n')
    result=subprocess.run([str(ROOT/'.venv-skhash/bin/SKHASH'),str(D/'control.txt')],cwd=ROOT,capture_output=True,text=True,timeout=300);(D/'skhash.log').write_text(result.stdout+result.stderr)
    sol=pd.read_csv(D/'solutions.csv') if (D/'solutions.csv').exists() else pd.DataFrame()
    counts=[]
    for eid,g in f.groupby('event_id'):
        pg=g[g.polarity_accepted];az=np.sort(pg.azimuth);gap=float(np.diff(np.r_[az,az[0]+360]).max()) if len(az) else 360
        counts.append(dict(event_id=int(eid),local_vertical_stations=len(g),reviewed_waveforms=len(g),accepted_ai_polarities=len(pg),accepted_ai_sp=int(g.sp_accepted.sum()),human_reviews=0,polarity_azimuth_gap_deg=gap,unmet_requirement='Fewer than 8 reliable first motions' if len(pg)<8 else f'Check SKHASH geometry/model acceptance; measured polarity gap {gap:.3f} degrees',scientifically_accepted=False))
    pd.DataFrame(counts).to_csv(D/'candidate_requirements.csv',index=False)
    summary=dict(candidates=len(counts),station_event_records=len(f),accepted_ai_polarities=int(f.polarity_accepted.sum()),accepted_ai_sp_ratios=int(f.sp_accepted.sum()),human_manual_reviews=0,returncode=result.returncode,computed_solutions=len(sol),accepted_scientific_mechanisms=0,classification='Exploratory; AI visual review, own provisional locations/model, explicit amplitude windows. Generic minimum-eight/90-degree/60-degree gates retained.',sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [D/'measurements.csv',DECISIONS,D/'velocity.csv',D/'control.txt']})
    (D/'skhash_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary);print(result.stdout[-2500:]);print(result.stderr[-1000:])
    if result.returncode:raise SystemExit(result.returncode)
if __name__=='__main__':main()
