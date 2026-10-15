"""Update live coverage after completed transfers; finish processing on collection stop.

This is one local process, not another agent. No new download is initiated here.
The collector alone applies storage/service limits. All later results use a new
versioned directory and retain the current scientific checkpoint on failure.
"""
import argparse,datetime,json,os,subprocess,time
from pathlib import Path
import availability_extension as a
def alive(pid):
    try:return b'availability_extension.py\x00retrieve' in Path(f'/proc/{pid}/cmdline').read_bytes()
    except FileNotFoundError:return False
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--collector-pid',type=int,required=True);x=ap.parse_args();previous=None;state=a.D/'continuation_status.json'
    while True:
        c=a.database();counts=dict(c.execute('SELECT status,count(*) FROM requests GROUP BY status').fetchall());c.close()
        running=alive(x.collector_pid)
        if counts!=previous or not running:
            # The collector writes a coherent coverage snapshot after each batch.
            # Avoid two processes rewriting those tables concurrently.
            coverage=json.loads((a.D/'coverage_summary.json').read_text()) if running else a.summarize()
            a.dump(state,dict(pid=os.getpid(),collector_pid=x.collector_pid,collector_running=running,request_states_now=counts,coverage=coverage,next='After the collector stops, freeze all completed observations, process them, refit and validate a new model, locate events, and rebuild the existing documents. No success claimed in advance.'));previous=counts
        if not running:break
        time.sleep(15)
    # Release the picking daemon after its current bounded batch. The frozen
    # processor obtains the same lock and completes remaining eligible files.
    (a.I/'stop_incremental_picking').write_text('Collector stopped; frozen continuation takes over.\n')
    tag=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')
    command=[str(a.ROOT/'.venv/bin/python'),'scripts/rebuild_availability_extension.py','--run-analysis','--catalog','data/availability_extension/catalog_'+tag,'--profile','data/availability_extension/velocity_'+tag]
    logfile=a.ROOT/'tmp/availability_extension'/('automatic_completion_'+tag+'.log')
    with logfile.open('w') as f:r=subprocess.run(command,cwd=a.ROOT,stdout=f,stderr=subprocess.STDOUT)
    a.dump(state,dict(pid=os.getpid(),collector_pid=x.collector_pid,collector_running=False,completion_command=command,returncode=r.returncode,log=str(logfile.relative_to(a.ROOT)),status='Document rebuild finished; scientific acceptance must be read from the model validation.' if r.returncode==0 else 'Completion computation failed; earlier checkpoint preserved. Inspect the saved log.'))
if __name__=='__main__':main()
