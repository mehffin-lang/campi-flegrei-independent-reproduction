"""Permitted routine-catalog panels and original RITE displacement observations.

This module does not import, seed or alter the independently detected catalog.
The HTML inputs are a dated external catalog snapshot, not Tan's Data S1--S3.
"""
from pathlib import Path
import hashlib
import io
import json
import re
import subprocess
import zipfile

import numpy as np
import pandas as pd
from lxml import html
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/continuation'
PROJ = Transformer.from_crs('EPSG:4326', '+proj=aeqd +lat_0=40.82 +lon_0=14.14 +datum=WGS84 +units=km', always_xy=True)


def main():
    OUT.mkdir(exist_ok=True)
    text = subprocess.check_output(['antiword', '-w', '250', str(ROOT/'inputs/extended/delgaudio2010_table.doc')], text=True)
    levels = []
    for line in text.splitlines():
        parts = [s.strip() for s in line.split('|')]
        if len(parts) > 6 and re.fullmatch(r'\d\d\??/\d{4}', parts[1]):
            month, year = map(int, parts[1].replace('?', '').split('/'))
            levels.append(dict(date=f'{year:04d}-{month:02d}-15', source_month_year=parts[1],
                               date_convention='15th is display placement; original reports month only',
                               month_uncertain='?' in parts[1], elevation_m=float(parts[2]),
                               source_uncertainty_text=parts[3], source=parts[6]))
        elif levels and len(parts) > 6 and not parts[1]:
            levels[-1]['source'] += ' ' + parts[6]
    lev = pd.DataFrame(levels)
    lev['source'] = lev.source.str.replace(r'\s+', ' ', regex=True).str.strip()
    lev['provenance_class'] = np.where(lev.source.str.contains('reconstruction',case=False),
        'source-provided reconstruction',np.where(lev.source.str.contains('estimate',case=False),
        'source-provided estimate','leveling survey'))
    lev['source_file']='inputs/extended/delgaudio2010_table.doc'
    lev['uncertainty_note']='Source heading says sigma(mm) but entries are decimal; retained verbatim, not converted or used as weights.'
    lev['displacement_from_1905_m'] = lev.elevation_m - lev.elevation_m.iloc[0]
    lev.to_csv(OUT/'historical_leveling.csv', index=False)
    gnss = pd.read_csv(ROOT/'inputs/continuation/RITE_daily.txt', sep=r'\s+', header=None, names=['mjd', 'up_m', 'up_sigma_m'])
    assert gnss.shape[1] == 3 and gnss.notna().all().all()
    assert gnss.mjd.is_monotonic_increasing and gnss.mjd.is_unique
    gnss['time'] = pd.to_datetime(gnss.mjd, unit='D', origin='1858-11-17', utc=True)
    offsets = []
    for row in lev.itertuples():
        t = pd.Timestamp(row.date, tz='UTC')
        near = gnss[(gnss.time >= t-pd.Timedelta(days=15)) & (gnss.time <= t+pd.Timedelta(days=15))]
        if len(near):
            offsets.append(dict(date=row.date, n_gnss=len(near), offset_m=row.displacement_from_1905_m-float(near.up_m.median())))
    offset = pd.DataFrame(offsets)
    assert len(offset) >= 3
    datum = float(offset.offset_m.median())
    gnss['displacement_from_1905_m'] = gnss.up_m + datum
    gnss['leveling_datum_m']=gnss.displacement_from_1905_m+float(lev.elevation_m.iloc[0])
    gnss['source']='Zenodo 17132077; RITE_daily.txt'
    gnss.to_csv(OUT/'rite_gnss_through2024.csv', index=False)
    offset.to_csv(OUT/'gnss_datum_alignment.csv', index=False)
    # Compare two independently released observation series on common days;
    # neither is a digitized line or a fitted Tan result.
    with zipfile.ZipFile(ROOT/'inputs/extended/demartino_supp.zip') as z:
        old = pd.read_csv(io.BytesIO(z.read('RITE_daily.txt')), sep=r'\s+', header=None,
                          names=['mjd','north','east','up_m','nsigma','esigma','usigma'])
    common = gnss.merge(old[['mjd','up_m']], on='mjd', suffixes=('_new','_old'))
    difference = common.up_m_new-common.up_m_old
    datum_change = float(difference.median())
    common[['mjd','up_m_new','up_m_old']].to_csv(OUT/'gnss_release_overlap.csv', index=False)
    # New official homogeneous release supplies the missing 2025 observations.
    # Estimate its constant datum from overlap, not from a published plot.
    newer=pd.read_csv(ROOT/'inputs/continuation/RITE_2000_2025.txt',sep=r'\s+',header=None,
                      names=['mjd','north_m','east_m','up_m','north_sigma_m','east_sigma_m','up_sigma_m'])
    newer['time']=pd.to_datetime(newer.mjd,unit='D',origin='1858-11-17',utc=True)
    joint=gnss[['mjd','displacement_from_1905_m']].merge(newer[['mjd','up_m']],on='mjd')
    shift=joint.displacement_from_1905_m-joint.up_m
    extension_offset=float(shift.median())
    newer['displacement_from_1905_m']=newer.up_m+extension_offset
    newer['leveling_datum_m']=newer.displacement_from_1905_m+float(lev.elevation_m.iloc[0])
    newer['source']='Zenodo 22259337; RITE_2000_2025.txt'
    newer.to_csv(OUT/'rite_release_2000_2025.csv',index=False)
    extension=newer[(newer.time>=pd.Timestamp('2025-01-01',tz='UTC'))&(newer.time<pd.Timestamp('2025-03-21',tz='UTC'))]
    gnss=pd.concat([gnss,extension[gnss.columns]],ignore_index=True)
    assert gnss.mjd.is_unique and gnss.mjd.is_monotonic_increasing
    gnss.to_csv(OUT/'rite_gnss.csv',index=False)

    events = []
    provenance = []
    for file in sorted((ROOT/'inputs/continuation').glob('routine_*.html')):
        raw = file.read_bytes()
        provenance.append(dict(file=str(file.relative_to(ROOT)), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
        tree = html.fromstring(raw)
        for row in tree.xpath('//tbody[@id="eventsbody"]/tr'):
            ident = row.get('id','').replace('event_','')
            fields = {e.get('id'): e.text_content().strip() for e in row.iter() if e.get('id')}
            def value(prefix):
                try: return float(fields[prefix+'_'+ident])
                except (KeyError, ValueError): return np.nan
            epoch = value('epoch')
            if not np.isfinite(epoch): continue
            t = pd.Timestamp(epoch, unit='s', tz='UTC')
            if not (pd.Timestamp('2005-01-01', tz='UTC') <= t < pd.Timestamp('2025-03-21', tz='UTC')): continue
            magnitudes = [v for k,v in fields.items() if re.fullmatch('magv_'+re.escape(ident)+r'_\d+_D', k)]
            try: md = float(magnitudes[0])
            except (IndexError, ValueError): md = np.nan
            events.append(dict(id=ident, time=t.isoformat(), longitude=value('lon'), latitude=value('lat'), depth_km=value('dep'), Md=md,
                               quality=fields.get('qual_'+ident,''), publication_class=row.get('class',''), source=str(file.relative_to(ROOT))))
    cat = pd.DataFrame(events).drop_duplicates('id').sort_values('time').reset_index(drop=True)
    assert len(cat) > 10000 and cat.id.is_unique
    cat['x_km'], cat['y_km'] = PROJ.transform(cat.longitude.to_numpy(), cat.latitude.to_numpy())
    cat.to_csv(OUT/'routine_catalog.csv', index=False)
    located = cat[np.isfinite(cat[['longitude','latitude','depth_km']]).all(axis=1)].copy()
    located.to_csv(OUT/'figure_1A.csv', index=False)
    times = pd.to_datetime(cat.time, utc=True, format='ISO8601')
    monthly = cat.assign(month=times.dt.strftime('%Y-%m')).groupby('month').agg(events=('id','size'), above_Md02=('Md',lambda x: int((x > .2).sum())))
    months = pd.period_range('2005-01', '2025-03', freq='M').astype(str)
    monthly = monthly.reindex(months, fill_value=0).rename_axis('month').reset_index()
    monthly['cumulative_above_Md02'] = monthly.above_Md02.cumsum()
    monthly['partial_month'] = monthly.month.eq('2025-03')
    monthly['bin_start']=pd.to_datetime(monthly.month+'-01',utc=True)
    monthly['bin_end']=monthly.bin_start+pd.offsets.MonthBegin(1)
    monthly.loc[monthly.partial_month,'bin_end']=pd.Timestamp('2025-03-21',tz='UTC')
    monthly['bin_days']=(monthly.bin_end-monthly.bin_start).dt.total_seconds()/86400
    monthly.to_csv(OUT/'figure_1C.csv', index=False)
    cumulative=cat[cat.Md>.2][['id','time','Md']].copy();cumulative['cumulative']=np.arange(1,len(cumulative)+1)
    cumulative.to_csv(OUT/'figure_1C_cumulative.csv',index=False)
    study = located[pd.to_datetime(located.time,utc=True,format='ISO8601') >= pd.Timestamp('2022-01-21',tz='UTC')]
    study.to_csv(OUT/'figure_S5.csv', index=False)
    cat.assign(year=times.dt.year, located=np.isfinite(cat[['longitude','latitude','depth_km']]).all(axis=1)).groupby('year').agg(events=('id','size'), located=('located','sum')).to_csv(OUT/'routine_annual_counts.csv')
    # Counts are measured after the written selection, never forced to a target.
    summary = dict(gnss_rows=len(gnss), gnss_start=str(gnss.time.min()), gnss_end=str(gnss.time.max()),
                   gnss_missing_calendar_days=int(gnss.mjd.max()-gnss.mjd.min()+1-len(gnss)),
                   gnss_datum_offset_m=datum, overlap_leveling_epochs=len(offset),
                   overlap_offset_mad_m=float(abs(offset.offset_m-datum).median()),
                   old_release_common_days=len(common), old_release_median_datum_difference_m=datum_change,
                   old_release_demeaned_difference_rms_m=float(np.sqrt(np.mean((difference-datum_change)**2))),
                   gnss_end_displacement_from_1905_m=float(gnss.displacement_from_1905_m.iloc[-1]),
                   historical_leveling_reference_m=float(lev.elevation_m.iloc[0]),
                   gnss2025_extension_rows=len(extension),gnss2025_release_rows=len(newer),gnss2025_release_end=str(newer.time.max()),
                   gnss2025_overlap_days=len(joint),gnss2025_datum_offset_m=extension_offset,
                   gnss2025_overlap_demeaned_rms_m=float(np.sqrt(np.mean((shift-extension_offset)**2))),
                   leveling_rows=len(lev), historical_provenance_counts=lev.provenance_class.value_counts().to_dict(),
                   routine_events=len(cat), routine_located=len(located),
                   routine_study_all=int((times>=pd.Timestamp('2022-01-21',tz='UTC')).sum()),
                   routine_study_located=len(study), published_study_located=12083,
                   located_count_difference_from_publication=len(study)-12083,
                   routine_Md_ge4=int((located.Md>=4).sum()), published_Md_ge4=5,
                   figure_1C_cumulative_Md_gt02=int((cat.Md>.2).sum()),
                   routine_snapshot='Retrieved 2026-10-12; live reviewed catalog, historical snapshot used by Tan not supplied',
                   count_difference_explanation='The current live catalog differs from the published snapshot. Revisions and unspecified selection may contribute; their separate effects cannot be established without the historical snapshot. No count matching/filter tuning was applied.',
                   selection='1A: located 2005-01-01 <= time < 2025-03-21; stars Md >=4. 1C: all monthly counts, cumulative strictly Md >0.2. S5: located 2022-01-21 <= time < 2025-03-21. No additional geographic or quality filter stated in these captions.',
                   role='External routine catalog expressly permitted for 1A,1C,S5 and documented post-detection Md calibration; isolated from picking and association.')
    assert int(monthly.events.sum()) == len(cat)
    assert int(monthly.cumulative_above_Md02.iloc[-1]) == int((cat.Md>.2).sum())
    (OUT/'context_summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    (ROOT/'docs/context_input_checksums.json').write_text(json.dumps(provenance,indent=2)+'\n')
    print(json.dumps(summary,indent=2))


if __name__ == '__main__': main()
