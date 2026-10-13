"""Isolated synthetic assertions: never imported by empirical data generation."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from differential_times import delay
import numpy as np
from scipy.signal import butter,sosfiltfilt
rng=np.random.default_rng(312);x=sosfiltfilt(butter(4,[2,14],fs=100,btype='bandpass',output='sos'),rng.normal(size=600))
# Take shifts from the same longer realization, avoiding circular wrapping.
a=x[200:400];b=x[193:393]
same=delay(a,a);forward=delay(a,b);reverse=delay(b,a)
fractional=delay(a,np.interp(np.arange(600)-7.35,np.arange(600),x)[200:400])
assert abs(same['delay_y_minus_x_s'])<1e-12
assert abs(forward['delay_y_minus_x_s']-.07)<.001
assert abs(forward['delay_y_minus_x_s']+reverse['delay_y_minus_x_s'])<1e-10
assert abs(fractional['delay_y_minus_x_s']-.0735)<.001
result=dict(passed=True,classification='Synthetic test only; not an observation or figure result',same=same,forward=forward,reverse=reverse,fractional=fractional,known_fractional_delay_s=.0735,fractional_error_tolerance_s=.001)
(ROOT/'tests/results/differential_time_assertions.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: zero lag, known 0.07 and 0.0735 s delays and pair reversal')
