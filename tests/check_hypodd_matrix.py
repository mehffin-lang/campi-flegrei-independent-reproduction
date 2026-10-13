"""Isolated arithmetic fixture: m>n used to fail the method's bounds check."""
from pathlib import Path
import subprocess,json
import numpy as np
ROOT=Path(__file__).resolve().parents[1];work=ROOT/'tmp/calibration_followup/matrix_test';work.mkdir(exist_ok=True)
(work/'test.f90').write_text('''program check_matrix
implicit none
double precision a(3,2)
real b(2), c(3)
a=reshape([1d0,2d0,3d0,4d0,5d0,6d0],[3,2])
b=[2.0,-1.0]
call matmult2(3,3,2,a,b,c)
print *,c
end program
''')
cmd=['gfortran','-fcheck=bounds',str(work/'test.f90'),str(ROOT/'build/hypodd21/src/hypoDD/matmult2.f'),'-o',str(work/'check')]
subprocess.run(cmd,check=True);out=subprocess.check_output([str(work/'check')],text=True)
got=np.fromstring(out,sep=' ');expected=np.array([[1.,4.],[2.,5.],[3.,6.]])@np.array([2.,-1.])
assert np.array_equal(got,expected)
result=dict(classification='synthetic arithmetic software test only; not observations or a scientific panel',passed=True,output=got.tolist())
(ROOT/'tests/results/hypodd_matrix.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
