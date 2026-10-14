"""Check delivered numerical, figure and document links without new analysis."""
from pathlib import Path
import hashlib,json,subprocess
import pandas as pd

ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/eida_continuation'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    rebuild=read(D/'rebuild_result.json');documents=read(ROOT/'report/document_build.json')
    assert rebuild['passed'] and documents['build_passed']
    checked=0
    for name,h in read(D/'numerical_checkpoint.json')['files'].items():
        # Original large inputs were checked by the just-completed default build.
        if name.startswith('inputs/'):continue
        assert sha(ROOT/name)==h,name
        checked+=1
    inventory=read(D/'plot_inventory.json')
    for item in inventory:
        for name,h in dict(item['inputs'],**item['outputs']).items():assert sha(ROOT/name)==h,name
    panels=read(ROOT/'docs/panel_record.json');assert len(panels)==len({r['panel'] for r in panels})==63
    for row in panels:
        if row['status']=='partially reproduced':assert (ROOT/row['generated_figure']).is_file(),row['panel']
    old=['data/local_extension','data/coverage_extension','data/mechanism_followup']
    assert not subprocess.check_output(['git','diff','--name-only','HEAD','--',*old],cwd=ROOT,text=True).strip()
    p=pd.read_csv(D/'picks.csv',usecols=['phase']);s=read(D/'analysis_summary.json')
    assert len(p)==s['picks'] and p.phase.eq('P').sum()==s['p_picks'] and p.phase.eq('S').sum()==s['s_picks']
    m=read(ROOT/'data/mechanism_eida/skhash_summary.json');r=pd.read_csv(ROOT/'data/mechanism_eida/review_decisions.csv')
    assert r.polarity_accepted.sum()==m['accepted_ai_polarities'] and r.sp_accepted.sum()==m['accepted_ai_sp_ratios']
    assert not r.human_reviewed.any()
    c=pd.read_csv(D/'processed_coverage.csv');period=[str(pd.to_datetime(c.start.min(),unit='s',utc=True)),str(pd.to_datetime(c.end.max(),unit='s',utc=True))]
    result=dict(passed=True,scientifically_accepted=False,post_build_noninput_hashes_checked=checked,
                original_input_hash_check='Executed by scripts/rebuild_eida_followup.py before plotting; no new retrieval occurred during the build.',
                figures_checked=len(inventory),panel_views=len(panels),panel_status_counts=pd.Series([r['status'] for r in panels]).value_counts().to_dict(),
                previous_numerical_checkpoints_unchanged=old,returned_observation_extrema_UTC=period,
                observation_extrema_warning='Endpoints do not imply intervening coverage; use union intervals and request ledger.',
                current_picks=len(p),reviewed_AI_polarities=int(r.polarity_accepted.sum()),reviewed_AI_SP=int(r.sp_accepted.sum()),human_reviews=0,
                report_pages=documents['report_pages'],comparison_pages=documents['comparison_pages'],
                published_images_only_in_comparison=documents['published_images_only_in_comparison'],
                PDFs={f'report/{n}.pdf':sha(ROOT/f'report/{n}.pdf') for n in ['report','comparison']},
                visual_inspection='Recorded separately after rendering the delivered PDFs; not inferred by this numerical check.')
    (D/'delivery_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':main()
