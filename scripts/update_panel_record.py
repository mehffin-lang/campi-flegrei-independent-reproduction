from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
rows=json.loads((root/'docs/panels.json').read_text())
for r in rows:
 p=r['panel'];r['input_observation_files']=[]
 r['status']='not reproduced';r['data_command']=None;r['plot_command']=None
 r['attempt']='Written-method audit followed by actual FDSN retrieval and independent inference; this panel is not numerically generated unless marked partial.'
 r['blocker']='Unfinished full-period processing and missing calibrated/relocated catalog. Provisional GaMMA diagnostics use an alternative external profile; they are not this panel. Author-derived results are not substituted.'
 if p in ['1A','1C'] or p.startswith('S5'):
  r['blocker']='External routine-catalog context is plotted and labeled separately. It is not an independently detected historical catalog or a reproduced analysis result.'
  r['comparison_data_command']='.venv/bin/python scripts/context_data.py'
  r['comparison_plot_command']='.venv/bin/python scripts/plot_extended.py'
  r['comparison_figure']='figures/routine_catalog_context.pdf' if p.startswith('S5') else 'figures/historical_catalog_context.pdf'
 if p=='1B':
  for key in ['comparison_data_command','comparison_plot_command','comparison_figure']:r.pop(key,None)
  r.update(status='partially reproduced',data_command='.venv/bin/python scripts/context_data.py',plot_command='.venv/bin/python scripts/plot_extended.py',input_observation_files=['inputs/extended/delgaudio2010_table.doc','inputs/extended/demartino_supp.zip','inputs/extended/monthly_2023_12.pdf'],generated_figure='figures/historical_leveling_partial.pdf',blocker='Original leveling table independently extracted and referenced to March 1905; 128 entries through July 2009. Original RITE GNSS data through 2019 are independently aligned using overlapping leveling epochs; 2020--2023 daily observations remain missing.',attempt='Numerical observation-table extraction and plotting executed; no digitization.')
 if p.startswith('S3'):r['blocker']='Exact training traces and labels not identified from permissible metadata. Retraining was not repeated; permitted trained weights used for inference only.'
 if p.startswith('S4'):
  r['blocker']='Original and retrained models both executed on independently selected CSOB/CMIS calendar windows. Exact published windows and independent reference annotations remain unidentified; these diagnostics are not the published benchmark.'
  r['comparison_data_command']='.venv/bin/python scripts/compare_pickers.py';r['comparison_plot_command']='.venv/bin/python scripts/compare_pickers.py'
  r['comparison_figure']='figures/picker_comparison_'+('CSOB' if p=='S4A' else 'CMIS')+'.pdf'
 if p.startswith('S14'):r['blocker']='All supported downloaded CAAM/COLB intervals were scanned; exposure is about one day, not three years. Four candidate review examples remain unconfirmed. Published cluster histories and cluster-relative magnitudes are not reproduced.'
 if p=='S15D':r['blocker']='Exact shallow VT example not identified by written method alone; no author catalog or plot values used to select it.'
 if p in ['S1','S2','S15A','S15B','S15C']:
  r['status']='partially reproduced' if p in ['S1','S2','S15C'] else 'not reproduced';r['data_command']='.venv/bin/python scripts/analyze_observations.py';r['plot_command']='.venv/bin/python scripts/plot_observations.py'
  r['attempt']='Numerical processing executed from permitted observations/metadata; saved outputs plotted.'
  if p=='S1':
   r['input_observation_files']=[x['file'] for x in json.loads((root/'docs/rebuild_inputs.json').read_text()) if x['file'].endswith('.mseed')];r['blocker']='Verified retrieved channel intervals only; full-period network collection remains unfinished and RAN credentials are unavailable.';r['generated_figure']='figures/coverage_partial.pdf';r['data_command']='.venv/bin/python scripts/extended_analysis.py';r['plot_command']='.venv/bin/python scripts/plot_extended.py'
  elif p=='S2':
   r['input_observation_files']=['inputs/metadata/channels.txt','inputs/models/stations.csv']+[x['file'] for x in json.loads((root/'docs/rebuild_inputs.json').read_text()) if '/responses/' in x['file']];r['plot_command']='.venv/bin/python scripts/plot_extended.py';r["blocker"]="51-station permitted metadata inventory differs from the paper's 48-station description; exact epoch/membership and basemap not reproduced.";r['generated_figure']='figures/stations_partial.pdf'
  else:
   label='E'+str('ABC'.index(p[-1])+1);r['input_observation_files']=['inputs/waveforms/'+label+'_CAAM.mseed','inputs/waveforms/'+label+'_COLB.mseed','inputs/metadata/response.xml'];r['blocker']='Written template times used; exact published example alignment, display filtering and spectral settings incompletely specified. Sensitivity-corrected velocities and stated independent display settings used.';r['generated_figure']='figures/hybrid_'+label+'.pdf'
   if p in ['S15A','S15B']:
    r['blocker']='Post-generation visual comparison shows a different published example from the written-method template used here. The generated family-template figure is related analysis, not reproduction of this panel.'
    r['attempt']='Generated a related observational template example; exact published panel not reproduced.'
 if p.startswith('S8'):r['blocker']='Independent amplitude/SNR measurements executed but no qualifying relative-magnitude edge; zero calibrated magnitudes. INGV Md is now a permitted required calibration reference; no catalog magnitudes fill missing results.'
 if p.startswith('4'):r['blocker']='Independent calibrated locations, reviewed polarities and gCAP configurations are missing; focal inversions not run. Data S3 actually contains 74 rows/58 gCAP entries, consistent with methods; caption says 55.'
 if p.startswith('S7'):r['blocker']='No independent relocated catalog or fitted 1D model for regional HypoDD SVD tests. Generic HypoDD source is accessible; scientific runs are unfinished.'
 if p.startswith('S6'):r['blocker']='Generic VELEST compiled. The small independent candidate set is insufficient to resolve the chosen layered velocities and station corrections; paper uses 373 calibration events. Inversion not executed.'
 if p.startswith('S12'):r['blocker']='CPOZ observations retrieved, but this provisional catalog contains zero independently associated CPOZ P arrivals. Internal S-P consistency calculated at other stations; relocated sector gathers and location validation remain unfinished.'
 r['notes']=r.get('notes','')
(root/'docs/panels.json').write_text(json.dumps(rows,indent=2)+'\n')
(root/'docs/panel_record.json').write_text(json.dumps(rows,indent=2)+'\n')
