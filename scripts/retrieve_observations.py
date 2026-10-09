"""Retrieve allowed inputs only; never read author event products or scripts."""
from pathlib import Path
import concurrent.futures,hashlib,json,subprocess,datetime
ROOT=Path(__file__).resolve().parents[1]
requests=[]
def add(path,url,kind): requests.append((path,url,kind))
base='https://webservices.ingv.it/fdsnws/'
add('metadata/channels.txt',base+'station/1/query?network=IV&minlatitude=40.7&maxlatitude=40.95&minlongitude=13.9&maxlongitude=14.3&starttime=2022-01-21&endtime=2025-03-21&level=channel&format=text','station metadata; epochs do not guarantee waveform coverage')
add('metadata/response.xml',base+'station/1/query?network=IV&station=CAAM,COLB,CSOB,CSTH&starttime=2022-01-21&endtime=2025-03-21&level=response','instrument metadata')
commit='f84c9c9dc6bb1501a95a833f6634199a63d4f3b3'
for f in ['phasenet_retrained.json','phasenet_retrained.pt','stations.csv']:
 add('models/'+f,'https://raw.githubusercontent.com/iamharrison2000/Campi-Flegrei-Earthquake-Monitoring/'+commit+'/models/'+f,'permitted model artifact' if 'phasenet' in f else 'station metadata')
# Times explicitly specified in the written template-method description, not read from a catalog.
for label,start,end in [('E1','2024-05-06T22:10:00','2024-05-06T22:13:00'),('E2','2024-03-08T17:40:00','2024-03-08T17:43:00'),('E3','2025-02-17T08:06:00','2025-02-17T08:09:00')]:
 for station in ['CAAM','COLB']:
  add('waveforms/'+label+'_'+station+'.mseed',base+'dataselect/1/query?net=IV&sta='+station+'&loc=*&cha=HH?&start='+start+'&end='+end,'raw waveform; written-method template window')
# A calendar-selected day, independent of all catalogs. Hourly chunks bound retries/memory.
for station in ['CAAM','COLB','CSOB','CSTH']:
 for hour in range(24):
  start=datetime.datetime(2024,1,1)+datetime.timedelta(hours=hour);end=start+datetime.timedelta(hours=1)
  add('waveforms/day_'+station+'_'+str(hour).zfill(2)+'.mseed',base+'dataselect/1/query?net=IV&sta='+station+'&loc=*&cha=HH?&start='+start.isoformat()+'&end='+end.isoformat(),'raw continuous waveform; calendar-selected validation day')
def retrieve(item):
 path,url,kind=item;p=ROOT/'inputs'/path;p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists() and p.stat().st_size>0: status='cached';code=0;error=''
 else:
  r=subprocess.run(['curl','-fLsS','--connect-timeout','15','--max-time','90','--retry','1','-o',str(p)+'.part','-w','%{http_code}',url],capture_output=True,text=True)
  status=r.stdout;code=r.returncode;error=r.stderr
  if code==0 and status=='200': Path(str(p)+'.part').replace(p)
 row=dict(file='inputs/'+path,url=url,kind=kind,http=status,returncode=code,error=error)
 if p.exists(): row.update(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 print(path,status,flush=True);return row
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: rows=list(pool.map(retrieve,requests))
 (ROOT/'docs/observation_inputs.json').write_text(json.dumps(rows,indent=2)+'\n')
