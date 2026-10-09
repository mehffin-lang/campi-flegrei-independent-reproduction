"""Build the report's tables from saved method outputs and reviewed documentation."""
from pathlib import Path
import csv,json
ROOT=Path(__file__).resolve().parents[1]
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
assert all(x['status']=='not reproduced' and x['data_command'] is None and x['plot_command'] is None for x in rows)
(ROOT/'data/panel_attempts.json').write_text(json.dumps({'records':len(rows),'reproduced':0,'partial':0,'numerically_executed_empirical_panels':0,'attempt_stage':'specification and allowed-input audit','all_records':rows},indent=2)+'\n')
table('panels_table.tex','Panel/view & Quantity & Specification, parameters and blocker',[[tex(x['panel']),tex(x['quantity']),tex(x['documentation']+'. '+x['parameters']+'. Blocked: '+x['blocker']+(' Note: '+x['notes'] if x['notes'] else ''))] for x in rows],r'>{\raggedright\arraybackslash}p{.14\linewidth}>{\raggedright\arraybackslash}p{.27\linewidth}>{\raggedright\arraybackslash}p{.49\linewidth}')
inv=json.loads((ROOT/'docs/file_inventory.json').read_text())
table('files_table.tex','File & Bytes & Inspection',[[r'\path{'+x['file']+'}',str(x['bytes']),tex('Text readable; '+('7 pages' if x['file']=='tanmodel.pdf' else '35 pages') if x['file'].endswith('.pdf') else 'Directory readable; CRC passed; not extracted or executed')] for x in inv],r'p{.52\linewidth}r p{.25\linewidth}')
