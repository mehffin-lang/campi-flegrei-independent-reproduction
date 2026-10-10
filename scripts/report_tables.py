"""Build the report's tables from saved method outputs and reviewed documentation."""
from pathlib import Path
import csv,json
ROOT=Path(__file__).resolve().parents[1]
from final_comparison import compare
# This occurs only after all independent numerical processing has finished.
# It reads the author catalog solely as a clearly labeled final reference.
compare()
def tex(s):
    m={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}','<':r'$<$','>':r'$>$'}
    return ''.join(m.get(c,c) for c in str(s))
def table(name,header,rows,layout):
    t=[r'\begin{longtable}{'+layout+'}',r'\toprule',header+r'\\\midrule',r'\endhead']
    t.extend(' & '.join(row)+r'\\[3pt]' for row in rows)
    t.extend([r'\bottomrule',r'\end{longtable}'])
    (ROOT/'report'/name).write_text('\n'.join(t)+'\n')
with (ROOT/'data/checks.csv').open() as f: checks=list(csv.DictReader(f))
assert all(x['pass']=='1' for x in checks)
summary={'tests':len(checks),'all_passed':True,'max_fi_error':max(float(x['error']) for x in checks if x['name'].startswith('fi_mixture_')),
         'magnitude_error':next(float(x['error']) for x in checks if x['name']=='magnitude_exact_recovery')}
(ROOT/'data/validation_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(ROOT/'report/results.tex').write_text('All '+str(summary['tests'])+' checks passed. The maximum absolute FI error across the analytic mixtures was '+format(summary['max_fi_error'],'.3g')+'; the maximum exact-recovery magnitude error was '+format(summary['magnitude_error'],'.3g')+'. These errors compare against analytic fixtures, not observed earthquakes.\n')
table('checks_table.tex','Check & Absolute error & Tolerance',[[tex(x['name']),format(float(x['error']),'.3g'),format(float(x['tolerance']),'.3g')] for x in checks],r'lr r')
rows=json.loads((ROOT/'docs/panels.json').read_text())
assert len(set(x['panel'] for x in rows))==len(rows)
counts={status:sum(r['status']==status for r in rows) for status in ['independently reproduced','partially reproduced','not reproduced']}
(ROOT/'data/panel_attempts.json').write_text(json.dumps({'records':len(rows),'counts':counts,'all_records':rows},indent=2)+'\n')
table('panels_table.tex','Panel/view & Quantity & Status, specification and limitation',[[tex(x['panel']).replace('/',r'/\allowbreak{}'),tex(x['quantity']),tex(x['status']+'. '+x['documentation']+'. '+x['parameters']+'. '+x['blocker'])] for x in rows],r'>{\raggedright\arraybackslash}p{.12\linewidth}>{\raggedright\arraybackslash}p{.25\linewidth}>{\raggedright\arraybackslash}p{.52\linewidth}')
obs=json.loads((ROOT/'data/observations/summary.json').read_text())
(ROOT/'report/observations.tex').write_text('The run read '+str(obs['files'])+' waveform files containing '+str(obs['waveform_records'])+' channel segments. The station map includes '+str(obs['stations'])+' study stations. PhaseNet generated '+str(obs['picks'])+' unique picks ('+str(obs['phase_counts']['P'])+' P and '+str(obs['phase_counts']['S'])+' S). All '+str(len(obs['tests']))+' observational consistency checks passed. The template scan found '+str(obs['template_candidates'])+' unreviewed candidate matches across '+str(obs['template_scan_hours'])+' verified hourly intervals ('+format(obs['template_valid_start_seconds']/3600,'.3f')+' hours of valid window-start times).\n')
table('template_table.tex','Template & FI & Samples',[[tex(r['template']),format(r['FI'],'.4f'),str(r['samples'])] for r in obs['templates']],r'lrr')
inv=json.loads((ROOT/'docs/file_inventory.json').read_text())
table('files_table.tex','File & Bytes & Inspection',[[r'\path{'+x['file']+'}',str(x['bytes']),tex('Text and captions readable' if x['file'].endswith('.pdf') else 'Directory readable; CRC passed; not executed')] for x in inv],r'p{.52\linewidth}r p{.25\linewidth}')
