"""Hash the current own numerical checkpoint and the actual inputs to its plots."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/eida_continuation';M=ROOT/'data/mechanism_eida'
def main():
    files={}
    for base in [D,M]:
        for p in base.rglob('*'):
            if not p.is_file() or p.suffix not in ['.csv','.json','.npz','.mod','.sta','.gz']:continue
            if p.name in ['numerical_checkpoint.json','rebuild_result.json','plot_inventory.json','panel_status.json','style.json','delivery_verification.json']:continue
            files[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
    for r in json.loads((D/'all_observation_inputs.json').read_text()):
        assert hashlib.sha256((ROOT/r['file']).read_bytes()).hexdigest()==r['sha256'],r['file']
        files[r['file']]=r['sha256']
    for name,h in json.loads((D/'processing_checkpoint.json').read_text())['files'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
        files[name]=h
    for name in ['inputs/continuation/IV_responses.xml','inputs/continuation/2I_responses.xml',
                 'data/eida_continuation/calibration/reference_grid.original',
                 'config/mechanism_review_arrivals.csv']:
        files[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    for pattern in ['*velest*.py','check_sparse32_eida.py','*tomodd*.py','*hypodd*.py','process_continuous.py','process_eida_followup.py','reuse_own_associations.py','gamma_reproducibility.py','calibration_chain.py','calibrate_eida_followup.py','grid_focal_attempt.py','eida_shallow_example.py','grid_uncertainty.py','grid_panel_data.py','grid_location_checks.py','downstream_checks.py','magnitude_statistics.py','mechanism_measurements.py','run_reviewed_skhash.py','run_gcap_followup.py','validate_mechanism_followup.py','extend_hybrid_scan.py','grid_hybrid_candidates.py','hybrid_candidate_metrics.py','validate_eida_holdout.py','diagnose_eida_precision.py','catalog_frequency*.py','review_eida_hybrids.py','link_eida_candidates.py','prepare_eida_mechanism_review.py']:
        for p in (ROOT/'scripts').glob(pattern):files[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
    for name in ['config/eida_calibration.json','config/mechanism_eida_decisions.json','config/mechanism_eida_arrivals.csv','scripts/review_eida_additional_onsets.py','scripts/review_eida_arrival_packets.py','scripts/finish_eida_mechanisms.py']:
        p=ROOT/name;files[name]=hashlib.sha256(p.read_bytes()).hexdigest()
    (D/'numerical_checkpoint.json').write_text(json.dumps(dict(classification='Own provisional numerical outputs; observations checked, all known selected snippets excluded from detection; not a scientifically accepted catalog',files=files),indent=2)+'\n')
    print('Sealed',len(files),'current numerical files.')
if __name__=='__main__':main()
