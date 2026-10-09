from pathlib import Path
import json
root=Path(__file__).resolve().parents[1]
rows=json.loads((root/'docs/panels.json').read_text())
for r in rows:
 p=r['panel'];r['input_observation_files']=[]
 r['status']='not reproduced';r['data_command']=None;r['plot_command']=None
 r['attempt']='Written-method audit followed by actual FDSN retrieval and independent inference; this panel is not numerically generated unless marked partial.'
 r['blocker']='No independent associated and relocated multi-year event catalog; author-derived catalogs and velocity estimates excluded. Downstream inversion not implemented.'
 if p.startswith('1') or p.startswith('S5'):
  r['blocker']='Routine catalog is allowed only for final comparison, not as plotted analytical input. No independent historical event catalog.'
 if p=='1B':r['blocker']='Historical displacement observations not retrieved; seismic waveform services do not supply this series.'
 if p.startswith('S3'):r['blocker']='Exact training traces and labels not identified from permissible metadata. Retraining was not repeated; permitted trained weights used for inference only.'
 if p.startswith('S4'):r['blocker']='Exact comparison windows and original-network baseline not established. Validation-day picks are not this published example.'
 if p.startswith('S14'):r['blocker']='Full three-year template search and manual review not performed. Three method-specified templates alone do not reproduce cluster history.'
 if p=='S15D':r['blocker']='Exact shallow VT example not identified by written method alone; no author catalog or plot values used to select it.'
 if p in ['S1','S2','S15A','S15B','S15C']:
  r['status']='partially reproduced' if p in ['S1','S2','S15C'] else 'not reproduced';r['data_command']='.venv/bin/python scripts/analyze_observations.py';r['plot_command']='.venv/bin/python scripts/plot_observations.py'
  r['attempt']='Numerical processing executed from permitted observations/metadata; saved outputs plotted.'
  if p=='S1':
   r['input_observation_files']=['inputs/waveforms/*.mseed'];r['blocker']='Actual retrieved intervals only; four stations and short windows, not full INGV/IDPC three-year coverage.';r['generated_figure']='figures/coverage_partial.pdf'
  elif p=='S2':
   r['input_observation_files']=['inputs/metadata/channels.txt','inputs/models/stations.csv'];r["blocker"]="51-station permitted metadata inventory differs from the paper's 48-station description; exact epoch/membership and basemap not reproduced.";r['generated_figure']='figures/stations_partial.pdf'
  else:
   label='E'+str('ABC'.index(p[-1])+1);r['input_observation_files']=['inputs/waveforms/'+label+'_CAAM.mseed','inputs/waveforms/'+label+'_COLB.mseed','inputs/metadata/response.xml'];r['blocker']='Written template times used; exact published example alignment, display filtering and spectral settings incompletely specified. Sensitivity-corrected velocities and stated independent display settings used.';r['generated_figure']='figures/hybrid_'+label+'.pdf'
   if p in ['S15A','S15B']:
    r['blocker']='Post-generation visual comparison shows a different published example from the written-method template used here. The generated family-template figure is related analysis, not reproduction of this panel.'
    r['attempt']='Generated a related observational template example; exact published panel not reproduced.'
 r['notes']=r.get('notes','')
(root/'docs/panels.json').write_text(json.dumps(rows,indent=2)+'\n')
(root/'docs/panel_record.json').write_text(json.dumps(rows,indent=2)+'\n')
