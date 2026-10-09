"""Record blocked publication-panel attempts without inventing panel identities."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
rows=json.loads((ROOT/'docs'/'panel_record.json').read_text())
assert not any(r['status']=='independently reproduced' and r['scope']!='validation' for r in rows)
result={'manuscript_panels_reproduced':0,'manuscript_panels_partial':0,
        'individual_panel_inventory_complete':False,'scientific_reproduction_complete':False,
        'attempts':rows}
(ROOT/'data'/'panel_attempts.json').write_text(json.dumps(result,indent=2)+'\n')
print('Publication audit: all manuscript and supplementary panels blocked; individual inventory unresolved.')
