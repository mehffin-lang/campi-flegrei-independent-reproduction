"""Auditable input retrieval. No author result tables or analysis scripts are read."""
from pathlib import Path
import argparse, concurrent.futures, hashlib, json, subprocess, urllib.parse

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://webservices.ingv.it/'

def fetch(item):
    name, url, kind = item
    path = ROOT / 'inputs/extended' / name
    path.parent.mkdir(parents=True, exist_ok=True)
    row = dict(file=str(path.relative_to(ROOT)), url=url, classification=kind)
    if path.exists() and path.stat().st_size:
        row.update(http='cached', returncode=0)
    else:
        part = Path(str(path)+'.part')
        result = subprocess.run(['curl','-L','-sS','--connect-timeout','20',
            '--max-time','180','--max-filesize','536870912','-o',str(part),
            '-w','%{http_code}',url], capture_output=True,text=True)
        row.update(http=result.stdout, returncode=result.returncode, error=result.stderr)
        if result.returncode == 0 and result.stdout == '200':
            part.replace(path)
        elif part.exists():
            row['incomplete_bytes'] = part.stat().st_size
            if part.stat().st_size < 10000:
                row['response'] = part.read_text(errors='replace')
            if name.endswith('.mseed') and part.stat().st_size > 10000:
                path=Path(str(path).replace('.mseed','.partial.mseed'))
                part.replace(path);row['file']=str(path.relative_to(ROOT))
                row['complete_request']=False
            else:
                part.unlink()
    if path.exists():
        row.update(bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    print(name,row['http'],row.get('bytes',0),flush=True)
    return row

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['sources','full-requests','day','responses','windows'])
    parser.add_argument('--date',default='2024-01-01')
    args=parser.parse_args(); jobs=[]
    def add(name,url,kind): jobs.append((name,url,kind))
    if args.mode=='sources':
        for name,url,kind in [
            ('ingv_landing.html','https://eida.ingv.it/it/network/IV','source description'),
            ('ran.html','https://ran.protezionecivile.it/IT/index.php','source description'),
            ('ran_login.html','https://ran.protezionecivile.it/IT/autenticazione.php','access requirements'),
            ('local.html','https://dataserver.ov.ingv.it/users/anna.tramelli/seismic_records/index.html','observation archive description'),
            ('zenodo.json','https://zenodo.org/api/records/16562216','release metadata; not analysis input'),
            ('calo2018.html','https://www.nature.com/articles/s41598-018-34456-x','external model written specification'),
            ('demartino2021.html','https://www.mdpi.com/2072-4292/13/14/2725','displacement source written specification'),
            ('delgaudio2010.html','https://doi.org/10.1016/j.jvolgeores.2010.05.014','historical displacement source'),
            ('battaglia2008.html','https://doi.org/10.1111/j.1365-2478.2007.00687.x','external background model source'),
            ('model_readme.md','https://raw.githubusercontent.com/iamharrison2000/Campi-Flegrei-Earthquake-Monitoring/f84c9c9dc6bb1501a95a833f6634199a63d4f3b3/README.md','method artifact descriptions'),
            ('background_3d_vmod','https://raw.githubusercontent.com/iamharrison2000/Campi-Flegrei-Earthquake-Monitoring/f84c9c9dc6bb1501a95a833f6634199a63d4f3b3/models/3d_vmod','candidate fixed external background model; provenance must be checked before use'),
        ]: add(name,url,kind)
        for net in ['IV','2I']:
            add('channels_'+net+'.txt',BASE+'fdsnws/station/1/query?'+urllib.parse.urlencode(dict(network=net,minlatitude=40.7,maxlatitude=40.95,minlongitude=13.9,maxlongitude=14.3,starttime='2022-01-21',endtime='2025-03-21',level='channel',format='text')),'station metadata')
        for year in range(2005,2026):
            add('routine_'+str(year)+'.html',f'https://terremoti.ov.ingv.it/gossip/flegrei/{year}/index.html','external routine catalog: final comparison and documented Md calibration only')
    else:
        import datetime
        study={line.split(',')[0].split('.')[1] for line in (ROOT/'inputs/models/stations.csv').read_text().splitlines()[1:]}
        channels={}
        for net in ['IV','2I']:
            p=ROOT/'inputs/extended'/('channels_'+net+'.txt')
            if not p.exists():continue
            for line in p.read_text().splitlines():
                if line.startswith('#'):continue
                v=line.split('|')
                if v[1] in study and v[3][:2] in ['HH','EH','SH']:
                    channels[(v[0],v[1])]=v[3][:2]
        if args.mode=='responses':
            for net,sta in channels:
                add('responses/'+net+'_'+sta+'.xml',BASE+'fdsnws/station/1/query?'+urllib.parse.urlencode(dict(network=net,station=sta,starttime='2022-01-21',endtime='2025-03-21',level='response')),'instrument response')
        else:
            start=args.date; end=(datetime.date.fromisoformat(start)+datetime.timedelta(days=1)).isoformat()
            if args.mode=='full-requests': start,end='2022-01-21','2025-03-21'
            if args.mode=='windows':start,end=start+'T12:00:00',start+'T12:30:00'
            for (net,sta),band in channels.items():
                add('waveforms/'+net+'_'+sta+'_'+start+'_'+end+'.mseed',BASE+'fdsnws/dataselect/1/query?'+urllib.parse.urlencode(dict(net=net,sta=sta,loc='*',cha='HH?,EH?,SH?',start=start,end=end)),'continuous original waveforms')
    receipt=ROOT/'docs'/('extended_'+args.mode+('_'+args.date if args.mode in ['day','windows'] else '')+'.json')
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for row in pool.map(fetch,jobs):
            rows.append(row);receipt.write_text(json.dumps(rows,indent=2)+'\n')

if __name__=='__main__':main()
