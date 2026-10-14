"""Run the existing documented solvers on the eligible EIDA checkpoint."""
import calibrate_local_followup as c
import os
import json

if __name__=='__main__':
    os.environ['CF_VELEST_TIMEOUT']='1800' # Expanded simultaneous location systems; unchanged convergence criteria.
    config=c.ROOT/'config/eida_calibration.json'
    if config.exists():os.environ['CF_VELEST_LAYER_DAMPING']=str(json.loads(config.read_text())['velocity_layer_damping'])
    c.D=c.ROOT/'data/eida_continuation';c.B=c.D/'calibration';c.W=c.ROOT/'tmp/eida_continuation'
    c.main()
