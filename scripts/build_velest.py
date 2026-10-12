"""Build official generic VELEST, retaining the upstream source unchanged."""
from pathlib import Path
import hashlib,json,os,subprocess,tarfile
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
os.environ['TMPDIR']=str(ROOT/'tmp')
archive=Path('inputs/extended/velest.tar')
with tarfile.open(archive) as f:
    names=f.getnames()
    allowed=['velest/velest.f','velest/vel_com.f','velest/velestmulti.cmn','velest/README']
    assert all(n in names for n in allowed)
    for name in allowed:
        p=Path('inputs/external')/name;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(f.extractfile(name).read())
s=Path('inputs/external/velest/velest.f').read_text()
assert "f6.1,)" in s
s=s.replace("f6.1,)","f6.1)")
# Replace only the platform CPU clock; no scientific calculation is changed.
s=s.replace('      icpu=clock()','      call cpu_time(cpu)\n      icpu=int(cpu*1000000.)')
s=s.replace('      integer icpu, clock','      integer icpu, clock\n      real cpu')
start=s.index('      subroutine DATETIME(dattim)')
end=s.index('      end ! of subroutine datetime',start)+len('      end ! of subroutine datetime')
s=s[:start]+'''      subroutine DATETIME(dattim)
      character*20 dattim
      character*8 d
      character*10 t
      call date_and_time(d,t)
      dattim=d//' '//t
      end
'''+s[end:]
Path('build/velest-portable.f').write_text(s)
header=Path('inputs/external/velest/vel_com.f').read_text()
assert 'parameter(ieq=658)' in header
Path('build/vel_com.f').write_text(header.replace('parameter(ieq=658)','parameter(ieq=1024)'))
cmd=['gfortran','-std=legacy','-O2','-fcheck=bounds','-fdefault-real-8','-fdefault-double-8','-I','build','build/velest-portable.f','-o','build/velest']
r=subprocess.run(cmd,capture_output=True,text=True)
record=dict(source_url='https://ethz.ch/content/dam/ethz/special-interest/erdw/geophysics/seismology-and-geodynamics-dam/document/velest.tar',source_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),command=cmd,returncode=r.returncode,output=r.stdout+r.stderr,changes=['Remove trailing comma in FORMAT','Replace SUN clock() with standard cpu_time','Replace SUN datetime with standard date_and_time','Increase declared simultaneous-event capacity from 658 to 1024; no equation change','Enable runtime array bounds checks','Use 64-bit real arithmetic after a recorded single-precision positive-definiteness failure; equations and damping unchanged'],event_capacity=1024,real_bits=64,scientific_execution=False)
Path('data/extended/velest_build.json').write_text(json.dumps(record,indent=2)+'\n')
print(record);r.check_returncode()
