"""Expose the executed coverage extension without mixing its event identifiers."""
from pathlib import Path
import json,hashlib,zipfile,re
import numpy as np
import pandas as pd
from pyproj import Transformer
import grid_report as gr
ROOT=gr.ROOT;D=ROOT/'data/coverage_extension';C=D/'calibration';R=ROOT/'report'
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def prepare():
    if not (C/'execution.json').exists():return None
    result=dict(processing=read(D/'analysis_summary.json'),coverage=read(D/'coverage_audit.json'),acquisition=read(D/'acquisition_summary.json'),execution=read(C/'execution.json'),numerical_panels={},scientific_acceptance=False)
    out=C/'merged4/panels';out.mkdir(exist_ok=True)
    proj=Transformer.from_crs('EPSG:4326','+proj=aeqd +lat_0=40.82 +lon_0=14.14 +datum=WGS84 +units=km',always_xy=True)
    for group,path in [('S6',C/'merged4/filtered_events.csv'),('3',C/'merged4/tomodd/round2_locations.csv')]:
        if not path.exists():continue
        e=pd.read_csv(path)
        if group=='3':e=e[e.gap_deg<=300].copy()
        if e.empty:continue
        e['x_km'],e['y_km']=proj.transform(e.longitude.to_numpy(),e.latitude.to_numpy());e['ML']=np.nan
        target=out/('velest.csv' if group=='S6' else 'relocated.csv')
        if not (out/'summary.json').exists():e.to_csv(target,index=False)
        result['numerical_panels'][group]=dict(events=len(e),source=str(path.relative_to(ROOT)),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),saved_data=str(target.relative_to(ROOT)),figure='figures/figure_'+group+'_extension.pdf',limitation='Separate new event IDs; no inherited magnitude or uncertainty. Unaccepted numerical trial, not additional independent confirmation.')
    if (out/'summary.json').exists():
        for group,path in [('2',out/'weekly_counts.csv'),('S7',C/'merged4/uncertainty/regional_svd.csv'),('S8',C/'merged4/magnitude/magnitudes.csv'),('S10',out/'relocated.csv'),('S11',out/'swarm-2.csv'),('S12',out/'cpoz_index.csv'),('S13',out/'relocated.csv')]:
            result['numerical_panels'][group]=dict(rows=len(pd.read_csv(path)),source=str(path.relative_to(ROOT)),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),saved_data=str(path.relative_to(ROOT)),figure='figures/figure_'+group+'_extension.pdf',limitation='Separate new event identifiers; independently rerun conditional analysis, not absolute validation.')
        for folder,file in [('uncertainty','summary.json'),('magnitude','magnitude_statistics.json'),('focal','summary.json'),('location_checks','summary.json')]:result[folder]=read(C/'merged4'/folder/file)
    for name in ['summary','validation']:
        p=C/'merged4'/(name+'.json')
        if p.exists():result[name]=read(p)
    common=[]
    def canonical_cnv(path):
        records=[]
        for block in path.read_text().strip().split('\n\n'):
            lines=block.splitlines();tokens=[]
            for line in lines[1:]:
                assert len(line)%12==0
                tokens.extend(line[i:i+12] for i in range(0,len(line),12))
            records.append((lines[0],sorted(tokens)))
        return records
    for region in ['caldera','Pozzuoli_Solfatara']:
        for name in ['input.cnv','input.mod','input.sta','velest.cmn']:
            a=ROOT/'tmp/grid_calibration/merged4'/(region+'_prelocation')/name;b=ROOT/'tmp/coverage_extension/merged4'/(region+'_prelocation')/name
            if a.exists() and b.exists():
                row=dict(region=region,file=name,identical=a.read_bytes()==b.read_bytes(),sha256=hashlib.sha256(a.read_bytes()).hexdigest(),extension_sha256=hashlib.sha256(b.read_bytes()).hexdigest())
                if name=='input.cnv':row['same_events_and_phase_multiset']=canonical_cnv(a)==canonical_cnv(b);row['difference']='CNV phase order can differ at tied arrival times; compare complete event headers and phase multisets.'
                common.append(row)
    if common:write(C/'common_calibration_inputs.json',common)
    members={}
    with zipfile.ZipFile(C/'run_records.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted((ROOT/'tmp/coverage_extension').rglob('*')):
            if p.is_file() and p.suffix not in ['.npz','.sqlite']:
                name=str(p.relative_to(ROOT/'tmp/coverage_extension'));z.write(p,name);members[name]=hashlib.sha256(p.read_bytes()).hexdigest()
    write(C/'run_records.json',members);write(D/'report_summary.json',result);return result
def integrate():
    x=prepare()
    if x is None:return
    a=x['processing'];coverage=x['coverage'];layout=read(R/'figure_layout.json');rows=read(ROOT/'docs/panel_record.json')
    short={
      '1':'External routine-catalog context and source-labeled leveling/GNSS observations. These earthquakes are not independent detections. Historical snapshot and datum differences remain.',
      '2':'Provisional weekly counts and depths from two overlapping own subsets. Sparse exposure is not a full-period rate measurement; spatial masks differ. Routine context has a separate axis.',
      '3':'Two separately processed 123-event trial subsets. Calibration sensitivity prevents accepting fault geometry. Own magnitudes set sizes where measured; crosses mark missing magnitudes. Depth colors retain over-range values.',
      'S6':'216 and 219 own VELEST numerical-filter passes. Uniform symbols and fixed 0–5 km depth colors; magenta marks deeper events. Calibration remains unaccepted; no author locations or fitted model are plotted.',
      'S7':'90 and 80 conditional SVD solutions from alternative quadrants. Kilometer-scale errors are retained. Different subset counts do not establish improved absolute accuracy.',
      'S8':'65 and 67 independently inverted amplitude magnitudes. Routine duration magnitude is a calibration prior, not validation. Completeness and b describe selected, discontinuous samples.',
      'S10':'Own trial locations by calendar year, with sparse coverage. Counts are not annual seismicity-rate estimates.',
      'S11':'Only swarm 2 contains retained own events. The other written calendar windows have no qualifying numerical result in either observed subset.',
      'S12':'118 and 122 original CPOZ component traces, aligned on own P picks and filtered above 4 Hz. Alternative geographic masks, individually normalized amplitudes and unreviewed onsets.',
      'S13':'Own provisional relocated coordinates on an independent coarse coastline. A satellite background is not implemented; no published pixels supply the result.',
      'S14':'Measured waveforms, frequency indices and amplitude ratios for the twelve highest correlations per template. These candidates are not confirmed hybrids or validated clusters.',
      'S15':'A/B use explicitly different E1/E2 examples; C uses the documented E3 template. All traces and spectra were computed from original observations. No qualified D example is available.'}
    for item in layout:
        if item['figure'] in short:item['comparison_caption']=short[item['figure']]
        if item['figure']=='S1':
            item['independent_files']=['figures/coverage_extension.pdf'];item['file_labels']=['S1: latest actual processed intervals']
            item['caption']=f'{a["files"]} files, {len(a["stations"])} station names and {a["processed_channel_hours"]:.3f} union channel-hours. Short interval markers do not imply full-period coverage. Earlier calibration/downstream cohort remains separately numbered.'
            for row in rows:
                if row['panel']=='S1':row.update(input_files=['data/coverage_extension/processed_coverage_union.json'],inputs=['data/coverage_extension/processed_coverage_union.json'],saved_data='data/coverage_extension/processed_coverage_union.json',output='figures/coverage_extension.pdf',output_files=['figures/coverage_extension.pdf'],data_command='.venv/bin/python scripts/extend_calibration_observations.py --workers 8 --output data/coverage_extension --reuse-own-days',blocker=item['caption'])
        if item['figure'] in x['numerical_panels']:
            q=x['numerical_panels'][item['figure']]
            if q['figure'] not in item['independent_files']:
                item['independent_files'].append(q['figure']);item['file_labels'].append('Latest extended cohort: independently rerun, provisional')
            item['caption']=item['caption'].split(' The additional extended-cohort view')[0]+' The additional extended-cohort view uses separately numbered, independently rerun results. Magnitudes and SVD uncertainties were not inherited by integer event ID.'
            for row in rows:
                if row['panel'] in item['partial_panels']:
                    row['additional_independent_results']=[dict(**q,data_command='.venv/bin/python scripts/calibrate_coverage_extension.py; .venv/bin/python scripts/coverage_extension_downstream.py; .venv/bin/python scripts/coverage_extension_report.py --prepare-only',plot_command='.venv/bin/python scripts/publication_plots.py')]
                    outputs=row.setdefault('output_files',[row.get('output',item['independent_files'][0])])
                    if q['figure'] not in outputs:outputs.append(q['figure'])
                    if q['saved_data'] not in row['input_files']:row['input_files'].append(q['saved_data'])
    write(R/'figure_layout.json',layout)
    for name in ['panel_record.json','panels.json']:write(ROOT/'docs'/name,rows)
    failed=x['execution'].get('failed_stage','None: all requested solver stages executed; scientific acceptance remains false')
    summary=x.get('summary',{});validation=x.get('validation',{})
    prose=f'The latest separately frozen extension contains {a["files"]} observed files from {len(a["stations"])} station names, {a["processed_channel_hours"]:.3f} union channel-hours, {a["picks"]:,} picks and {a["events"]:,} provisional associations ({a["assigned_picks"]:,} assigned picks). All returned study-period files in its manifest were processed. Instrument sensitivity and response stages cover all {coverage["response_covered_channel_hours"]:.3f} measured channel-hours; this checks epoch coverage, not absolute instrument calibration. The source-level gaps and failed/pending requests remain in its station-by-time ledger. Full-period acquisition remains unfinished, not demonstrated inaccessible. RAN waveform credentials remain unavailable.'
    own='; '.join(f'{group}: {q["events"]} provisional events' for group,q in x['numerical_panels'].items() if 'events' in q) or 'No complete current location panel returned'
    if 'uncertainty' in x:
        own+=f'; independently rerun downstream stages return {x["uncertainty"]["svd_events"]} conditional SVD estimates, {x["magnitude"]["magnitudes"]} amplitude magnitudes, {x["focal"]["solutions"]} mechanisms, and {x["location_checks"]["pairs"]} S-P pairs'
    tex=r'\section{Additional observed coverage and independent calibration trial}'+'\n'+gr.tex(prose)+'\n\n'+gr.tex(f'The same grid-derived inversion and relocation procedure was attempted on this cohort. {own}. Failed computational stage: {failed}. No prior cohort event ID is reused as a solution. The additional numerical views are explicitly provisional; the 90 SVD estimates, 65 magnitudes and CPOZ gathers elsewhere retain the frozen 1,015-association cohort. These counts must not be combined as separate earthquakes.')+'\n\n'+gr.tex('Unchanged daily association inputs reuse this implementation\'s own recorded solve only after checking the complete original checkpoint, station data, settings and exact multiset of numerical pick inputs. Identical-time row order and overlapping-file aliases can differ; indices are explicitly remapped to current original observations. Changed days run GaMMA again. This is not a claim that a new solve with another row ordering would be bitwise identical. A redundant association pass was interrupted and is not counted as complete.')+'\n\n'+r'Evidence and commands: \path{data/coverage_extension/processing_checkpoint.json}, \path{association_reuse.json}, \path{station_coverage.csv}, \path{unobserved_channel_intervals.csv}, \path{request_ledger.csv.gz} and \path{calibration/execution.json}, all under \path{data/coverage_extension/}. Run \path{scripts/freeze_coverage_extension.py} for the source ledger, \path{scripts/calibrate_coverage_extension.py} for the independent trial, and \path{scripts/publication_plots.py} for its saved numerical counterparts. Full executed solver controls and logs are preserved in \path{data/coverage_extension/calibration/run_records.zip}.'+'\n'
    tex=tex.replace('Evidence and commands:',r'\begingroup\small\raggedright Evidence and commands:')+r'\par\endgroup'+'\n'
    (R/'coverage_extension.tex').write_text(tex)
    if 'uncertainty' in x:
        u=x['uncertainty'];v=x['validation'];s=x['magnitude'];svd=pd.read_csv(C/'merged4/uncertainty/regional_svd.csv')
        extra=f'The extended-cohort full-path precision difference remains {v["precision_difference"]["max_depth_km"]:.2f} km in depth. Its 38-event calibration input multisets and controls match the earlier trial, with tied-phase ordering recorded explicitly; extra coverage therefore did not add calibration leverage. Between TomoDD rounds, maximum horizontal and depth shifts are {u["max_horizontal_m"]:.1f} m and {u["max_depth_km"]:.3f} km. Conditional SVD depth errors reach {svd.error_z_m.max()/1000:.3f} km. Their changed subset size is not proof of better absolute accuracy. Conditional magnitude statistics are Mc={s["Mc"]:.1f}, b={s["b"]:.3f} +/- {s["b_sigma"]:.3f}; they remain selected-subset descriptions, not population completeness.'
        with (R/'coverage_extension.tex').open('a') as out:out.write('\n'+gr.tex(extra.replace('Mc=-0.0','Mc=0.0'))+'\n')
    doc=R/'reproduction_documentation.tex';text=doc.read_text();tag=r'\input{report/coverage_extension.tex}'
    if tag not in text:text=text.replace(r'\input{report/provisional_validation.tex}',r'\input{report/provisional_validation.tex}'+'\n'+tag)
    doc.write_text(text)
    paper=R/'report.tex';text=paper.read_text();text=re.sub(r'Independent waveform processing produces .*?but has not established',lambda _:f'Independent waveform processing produces {a["events"]:,} provisional GaMMA associations from {a["picks"]:,} picks in the latest checkpoint, but has not established',text);paper.write_text(text)
    main=R/'main_paper.tex';text=main.read_text();note='Where two counterparts are shown, the first uses the frozen 1,015-association cohort and the second the latest 1,023-association cohort. They overlap and are not independent confirmations or additive event counts.'
    if note not in text:text=text.replace(r'\section*{Improving the earthquake catalog}',r'\section*{Improving the earthquake catalog}'+'\n'+note+'\n')
    main.write_text(text)
    stages=read(ROOT/'docs/stages.json');stages[0]['status']=prose;stages[1]['status']=f'Latest extension: {a["picks"]} own picks; frozen 1,015-association downstream cohort preserved separately.';stages[3]['status']=f'Latest extension: {a["events"]} provisional associations. Exact-data reuse of own daily solves and new changed-day runs are recorded; alternative association profile remains disclosed.';write(ROOT/'docs/stages.json',stages)
    write(D/'provenance.json',dict(observations='Original public waveforms and StationXML; exact files/intervals/hashes in input_jobs.json, retrieval_receipts.json and processing_checkpoint.json. No routine-catalog seed.',method_resources=['Permitted trained PhaseNet weights and documented generic GaMMA configuration, pinned in processing_checkpoint.json','Explicitly authorized unchanged Tan-distributed Battaglia-attributed grid; calibration/grid_provenance.json','Generic VELEST, TomoDD, HypoDD and SKHASH, with own controls and logs'],contextual_calibration='data/continuation/routine_catalog.csv used only after independent detection and location for magnitude priors.',own_results='picks.csv, associations.csv, initial_events.csv and calibration/merged4/ are computed by this implementation; reused daily solves come only from the hash-verified own earlier cohort.',published_results='None used as analysis inputs. Published figure crops occur only in report/comparison.pdf.',fixtures='No synthetic test observations enter these results. Zero magnitude/error fields in generic event-file formats are unused solver placeholders, not measured magnitudes or reported errors; plotted magnitudes come only from own amplitude inversion.',commands=['scripts/extend_calibration_observations.py --output data/coverage_extension --reuse-own-days','scripts/calibrate_coverage_extension.py','scripts/coverage_extension_downstream.py','scripts/publication_plots.py']))
    print(prose,own,failed)
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--prepare-only',action='store_true');args=p.parse_args()
    if args.prepare_only:prepare()
    else:integrate()
