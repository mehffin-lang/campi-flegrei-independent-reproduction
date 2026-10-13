"""Independent inference comparison on the caption-defined S4A swarm window.

The historical bulletin supplies context for the written example, not phase
labels or an event seed for the independently detected catalog.
"""
from pathlib import Path
import os,json,hashlib
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
os.environ.update(SEISBENCH_CACHE_ROOT=str(ROOT/'tmp/seisbench'),MPLCONFIGDIR=str(ROOT/'tmp/matplotlib'),OMP_NUM_THREADS='2')
import numpy as np
import torch
import seisbench.models as sbm
from obspy import read,UTCDateTime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
torch.set_num_threads(2)


def main():
    cfg=json.loads(Path('config/benchmark_window.json').read_text())
    start=UTCDateTime(cfg['start_utc']);seconds=cfg['duration_s'];source=Path(cfg['source_file'])
    st=read(str(source));st.merge(method=0);st=st.split()
    assert len(st)==3 and {tr.stats.channel for tr in st}=={'HHE','HHN','HHZ'}
    assert all(tr.stats.sampling_rate==100 and tr.stats.starttime<=start-15 and tr.stats.endtime>=start+seconds+15 for tr in st)
    vertical=st.select(component='Z')[0].copy().trim(start,start+seconds-.01)
    arrays=dict(time_s=vertical.times(),vertical_counts=vertical.data.astype(float))
    stream=st.copy();stream.detrend('demean');stream.filter('highpass',freq=1,corners=4,zerophase=False)
    records=[];picks=[]
    for name,metadata,weights in [('original','original.json.v1','original.pt.v1'),('retrained','phasenet_retrained.json','phasenet_retrained.pt')]:
        meta=Path('inputs/models')/metadata;weight=Path('inputs/models')/weights;spec=json.loads(meta.read_text())
        model=sbm.PhaseNet(**spec['model_args']);model.load_state_dict(torch.load(weight,weights_only=True,map_location='cpu'));model.eval();model.default_args.update(spec['default_args'])
        arguments=dict(model.default_args,P_threshold=.3,S_threshold=.3,batch_size=64)
        annotation=model.annotate(stream,**arguments);result=model.classify_aggregate(annotation,arguments)
        for phase in ['P','S']:
            tr=annotation.select(channel='*_'+phase)[0].copy().trim(start,start+seconds-.01)
            arrays[name+'_'+phase+'_time_s']=tr.times(reftime=start);arrays[name+'_'+phase]=tr.data
        for pick in result.picks:
            if start<=pick.peak_time<start+seconds:picks.append(dict(model=name,phase=pick.phase,time=str(pick.peak_time),probability=float(pick.peak_value)))
        records.append(dict(model=name,metadata=str(meta),metadata_sha256=hashlib.sha256(meta.read_bytes()).hexdigest(),weights=str(weight),weights_sha256=hashlib.sha256(weight.read_bytes()).hexdigest(),
                            counts={phase:sum(r['model']==name and r['phase']==phase for r in picks) for phase in ['P','S']}))
    out=Path('data/continuation');np.savez_compressed(out/'figure_S4A.npz',**arrays)
    (out/'figure_S4A_picks.json').write_text(json.dumps(picks,indent=2)+'\n')
    saved=np.load(out/'figure_S4A.npz');fig,axes=plt.subplots(4,1,figsize=(9,7),sharex=True)
    axes[0].plot(saved['time_s'],saved['vertical_counts'],color='.2',lw=.5);axes[0].set_ylabel('Raw counts')
    axes[1].specgram(saved['vertical_counts'],Fs=100,NFFT=256,noverlap=192,cmap='magma');axes[1].set(ylim=(0,25),ylabel='Frequency (Hz)')
    for ax,name in zip(axes[2:],['original','retrained']):
        for phase,color in [('P','#dc8734'),('S','#2e8876')]:ax.plot(saved[name+'_'+phase+'_time_s'],saved[name+'_'+phase],color=color,lw=.7,label=phase)
        ax.axhline(.3,color='.5',ls=':',lw=.7);ax.set(ylim=(0,1),ylabel=name+'\nprobability');ax.legend(fontsize=8,ncol=2)
    axes[-1].set(xlim=(0,seconds),xlabel='Seconds from '+str(start))
    fig.suptitle('S4A · Partial: independent CSOB inference comparison\nCaption-based start; exact published window and labeled accuracy unverified',fontsize=11)
    fig.tight_layout();fig.savefig('figures/figure_S4A.pdf');fig.savefig('figures/figure_S4A.png',dpi=150);plt.close(fig)
    summary=dict(**cfg,input_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),models=records,
        preprocessing='Demean, causal four-pole 1 Hz highpass; released normalization/default overlap/blinding; threshold 0.3. Raw Z spectrogram: 256 samples, 192 overlap.',
        authors_predictions_used=False,training_repeated=False,reference_phase_labels=False,accuracy_estimated=False)
    (out/'benchmark_window.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
