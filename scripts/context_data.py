"""External context and required Md reference, isolated from pick/association code."""
from pathlib import Path
import re,subprocess,json,zipfile,io
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/extended'
text=subprocess.check_output(['antiword','-w','250',str(ROOT/'inputs/extended/delgaudio2010_table.doc')],text=True)
(ROOT/'tmp/resume/level_table_wide.txt').write_text(text)
levels=[]
for line in text.splitlines():
    parts=[s.strip() for s in line.split('|')]
    if len(parts)>6 and re.fullmatch(r'\d\d\??/\d{4}',parts[1]):
        month,year=map(int,parts[1].replace('?','').split('/'))
        levels.append(dict(date=f'{year:04d}-{month:02d}-15',month_uncertain='?' in parts[1],
            elevation_m=float(parts[2]),source=parts[6]))
    elif levels and len(parts)>6 and not parts[1]:
        levels[-1]['source']+=' '+parts[6]
lev=pd.DataFrame(levels);assert len(lev)>50
lev['displacement_from_1905_m']=lev.elevation_m-lev.elevation_m.iloc[0]
lev.to_csv(OUT/'historical_leveling.csv',index=False)
# External GNSS input explicitly cited as reference 53 by Tan et al. Read only
# the observation member and its declared column format; never run archive code.
with zipfile.ZipFile(ROOT/'inputs/extended/demartino_supp.zip') as archive:
    assert archive.testzip() is None
    gnss=pd.read_csv(io.BytesIO(archive.read('RITE_daily.txt')),sep=r'\s+',header=None,
        names=['mjd','north_m','east_m','up_m','north_sigma_m','east_sigma_m','up_sigma_m'])
gnss['time']=pd.to_datetime(gnss.mjd,unit='D',origin='1858-11-17',utc=True)
# Estimate a datum offset only from overlapping independently published data.
# No Tan result or figure is consulted. Preserve both original series.
offsets=[]
for r in lev.itertuples():
    t=pd.Timestamp(r.date,tz='UTC');near=gnss[(gnss.time>=t-pd.Timedelta(days=15))&(gnss.time<=t+pd.Timedelta(days=15))]
    if len(near):offsets.append(r.displacement_from_1905_m-float(near.up_m.median()))
assert len(offsets)>=3
datum=float(np.median(offsets));gnss['displacement_from_1905_m']=gnss.up_m+datum
gnss.to_csv(OUT/'rite_gnss.csv',index=False)
bulletin=subprocess.check_output(['pdftotext','-layout',str(ROOT/'inputs/extended/monthly_2023_12.pdf'),'-'],text=True)
match=re.search(r'circa\s+(\d+)\s+cm da novembre 2005',bulletin)
assert match,'Written monitoring observation not found; do not digitize the plot'
uplift=float(match[1])/100
baseline=gnss[(gnss.time>=pd.Timestamp('2005-11-01',tz='UTC'))&(gnss.time<pd.Timestamp('2005-12-01',tz='UTC'))]
assert len(baseline)>10
pd.DataFrame([dict(time='2023-12-31',displacement_from_1905_m=float(baseline.displacement_from_1905_m.median())+uplift,uplift_since_nov2005_m=uplift,approximate=True,source='inputs/extended/monthly_2023_12.pdf; written deformation summary, not figure pixels')]).to_csv(OUT/'recent_displacement_endpoint.csv',index=False)
# Parse text fields only. Do not execute JavaScript or import author's picks.
events=[]
for file in sorted((ROOT/'inputs/extended').glob('routine_*.html')):
    soup=BeautifulSoup(file.read_text(),'html.parser')
    for row in soup.select('tbody#eventsbody tr'):
        ident=row.get('id','').replace('event_','')
        def val(prefix):
            node=row.find(id=prefix+'_'+ident)
            try:return float(node.get_text(strip=True))
            except (ValueError,AttributeError):return np.nan
        ts=val('epoch')
        if not np.isfinite(ts):continue
        t=pd.Timestamp(ts,unit='s',tz='UTC')
        if not (pd.Timestamp('2005-01-01',tz='UTC')<=t<pd.Timestamp('2025-03-21',tz='UTC')):continue
        mag=row.find(id=re.compile(r'^magv_'+re.escape(ident)+r'_\d+_D$'))
        try:md=float(mag.get_text(strip=True))
        except (ValueError,AttributeError):md=np.nan
        events.append(dict(id=ident,time=t.isoformat(),longitude=val('lon'),latitude=val('lat'),depth_km=val('dep'),Md=md,source=str(file.relative_to(ROOT))))
df=pd.DataFrame(events).drop_duplicates('id').sort_values('time')
df.to_csv(OUT/'external_routine_catalog.csv',index=False)
summary=dict(leveling_rows=len(lev),leveling_start=lev.date.min(),leveling_end=lev.date.max(),
    leveling_min_m=lev.displacement_from_1905_m.min(),leveling_max_m=lev.displacement_from_1905_m.max(),
    gnss_rows=len(gnss),gnss_start=str(gnss.time.min()),gnss_end=str(gnss.time.max()),gnss_datum_offset_m=datum,overlap_leveling_epochs=len(offsets),overlap_offset_mad_m=float(np.median(abs(np.array(offsets)-datum))),dec2023_written_uplift_since_nov2005_m=uplift,
    external_events=len(df),external_located=int(df.latitude.notna().sum()),
    external_study_events=int((pd.to_datetime(df.time,utc=True,format='ISO8601')>=pd.Timestamp('2022-01-21',tz='UTC')).sum()),
    external_role='Historical context/final comparison; Md may regularize independently measured magnitude differences under supplementary S6.',
    interpolated_gps_not_used='gps.dat is a later interpolated compilation, not original GPS observations')
(OUT/'context_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary)
