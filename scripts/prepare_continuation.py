"""Regenerate the verified published alternative table from its written source."""
from pathlib import Path
import hashlib,json
import pandas as pd
from lxml import html
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'inputs/continuation/tramelli2021.html'
h=html.fromstring(p.read_bytes());table=h.get_element_by_id('Tab1')
rows=[]
assert '1.78' in ' '.join(table.itertext())
for tr in table.xpath('.//tbody/tr'):
    values=[' '.join(x.itertext()).strip() for x in tr.xpath('./td')]
    if len(values)==2:
        vp,z=map(float,values);rows.append(dict(depth_top_km_bsl=z,vp_km_s=vp,vs_km_s=vp/1.78,vp_vs=1.78))
assert len(rows)==5 and [r['depth_top_km_bsl'] for r in rows]==[0,.5,1,3,10]
pd.DataFrame(rows).to_csv(ROOT/'data/continuation/alternative_starting_profile.csv',index=False)
meta=json.loads((ROOT/'config/alternative_starting_profile.json').read_text())
assert meta['source_sha256']==hashlib.sha256(p.read_bytes()).hexdigest()
print('Verified five layer tops, Vp (km/s), Vs=Vp/1.78; published alternative only.')
