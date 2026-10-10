"""Compare permitted trained artifacts on calendar-selected, unlabeled recordings.

This is an additional diagnostic, not the exact S4 benchmark or a training run.
Saved probability arrays, not published predictions, supply the plot.
"""
from pathlib import Path
import os,json
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
models={}
for name,meta,weights in [('original','original.json.v1','original.pt.v1'),('retrained','phasenet_retrained.json','phasenet_retrained.pt')]:
    spec=json.loads((ROOT/'inputs/models'/meta).read_text())
    net=sbm.PhaseNet(**spec['model_args'])
    net.load_state_dict(torch.load(ROOT/'inputs/models'/weights,map_location='cpu',weights_only=True));net.eval()
    net.default_args.update(spec['default_args']);models[name]=net
records=[]
for station,date,seconds in [('CSOB','2025-03-20',120),('CMIS','2024-01-01',1600)]:
    file=f'inputs/extended/waveforms/IV_{station}_{date}T12:00:00_{date}T12:30:00.mseed'
    start=UTCDateTime(date+'T12:00:15')
    st=read(file);st.merge(method=0);st=st.split()
    st.trim(start-15,start+seconds+15)
    assert len(st)==3 and all(tr.stats.sampling_rate==100 for tr in st)
    vertical=st.select(component='Z')[0].copy().trim(start,start+seconds-.01)
    data={'time':vertical.times(),'raw_vertical_counts':vertical.data.astype(float)}
    filtered=st.copy();filtered.detrend('demean');filtered.filter('highpass',freq=1,corners=4,zerophase=False)
    record=dict(station=station,input_file=file,start=str(start),seconds=seconds,reference_annotations=False)
    for name,net in models.items():
        annotation=net.annotate(filtered,batch_size=64)
        for phase in ['P','S']:
            tr=next(tr for tr in annotation if tr.stats.channel.endswith('_'+phase))
            tr.trim(start,start+seconds-.01)
            data[name+'_'+phase+'_time']=tr.times(reftime=start)
            data[name+'_'+phase]=tr.data.astype(float)
            finite=tr.data[np.isfinite(tr.data)]
            assert len(finite) and np.all((finite>=0)&(finite<=1))
            record[name+'_'+phase+'_maximum_probability']=float(finite.max())
        picks=net.classify(filtered,P_threshold=.3,S_threshold=.3,batch_size=64).picks
        record[name+'_pick_counts']={phase:sum(start<=p.peak_time<start+seconds and p.phase==phase for p in picks) for phase in ['P','S']}
    np.savez_compressed(f'data/extended/picker_comparison_{station}.npz',**data)
    records.append(record)
    # Plot only saved arrays so that the numerical provenance is inspectable.
    saved=np.load(f'data/extended/picker_comparison_{station}.npz')
    fig,axes=plt.subplots(4,1,figsize=(9,6),sharex=True)
    axes[0].plot(saved['time'],saved['raw_vertical_counts'],lw=.5,color='#333333');axes[0].set_ylabel('Raw counts')
    axes[1].specgram(saved['raw_vertical_counts'],Fs=100,NFFT=256,noverlap=192,cmap='magma');axes[1].set(ylim=(0,25),ylabel='Hz')
    for ax,name in zip(axes[2:],models):
        for phase,color in [('P','#dc8734'),('S','#2e8876')]:
            ax.plot(saved[name+'_'+phase+'_time'],saved[name+'_'+phase],color=color,lw=.7,label=phase)
        ax.axhline(.3,c='#777',ls=':',lw=.6);ax.set(ylim=(0,1),ylabel=name+'\nprobability');ax.legend(loc='upper right',fontsize=7,ncol=2)
    axes[-1].set(xlim=(0,seconds),xlabel='Seconds since '+str(start))
    fig.suptitle(station+' — independent unlabeled calendar window; not the published S4 example',fontsize=10)
    fig.tight_layout();fig.savefig(f'figures/picker_comparison_{station}.pdf');fig.savefig(f'figures/picker_comparison_{station}.png',dpi=160);plt.close(fig)
summary=dict(examples=records,training_repeated=False,accuracy_estimated=False,exact_published_examples=False,
    assumptions='Same causal four-pole 1 Hz highpass, released normalization/defaults, 0.3 threshold, 15 s context. Spectrogram 256 samples, 192 overlap; no reference picks or author predictions used.')
Path('data/extended/picker_comparison.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
