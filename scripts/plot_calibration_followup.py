"""Plot saved exploratory diagnostics, never publication-panel substitutes."""
import json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/calibration_followup'
os.environ['MPLCONFIGDIR']=str(ROOT/'tmp/matplotlib')
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def main():
    spans=json.loads((D/'expanded/processed_coverage_union.json').read_text());stations={}
    for row in spans:stations.setdefault('.'.join(row['channel'].split('.')[:2]),[]).extend(row['intervals'])
    fig,ax=plt.subplots(figsize=(9,6),layout='constrained')
    for i,(station,intervals) in enumerate(sorted(stations.items())):
        for a,b in intervals:
            ax.plot([mdates.date2num(pd.Timestamp(v,unit='s',tz='UTC')) for v in [a,b]],[i,i],color='#176b9a',lw=2)
    ax.set_yticks(range(len(stations)),sorted(stations),fontsize=7);ax.xaxis_date();ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.set(xlim=(pd.Timestamp('2022-01-21'),pd.Timestamp('2025-03-21')),title='S1 · Expanded actual processed intervals; gaps are not filled',xlabel='UTC date')
    fig.savefig(ROOT/'figures/followup_coverage.pdf');plt.close(fig)
    record=json.loads((D/'summary.json').read_text());path=json.loads((D/'convergence_path.json').read_text())
    move=[record['extra_pass_location_change']['max_horizontal_m']]+[r['change']['max_horizontal_m'] for r in path]
    runs={r['name']:r for r in record['runs']}
    rms=[runs['calibration_convergence']['event_rms_s']]+[r['event_rms_s'] for r in path]
    pd.DataFrame(dict(extra_pass=np.arange(1,6),max_horizontal_move_m=move,event_rms_aggregate_s=rms)).to_csv(D/'convergence_plot.csv',index=False)
    fig,axes=plt.subplots(1,2,figsize=(10,3.5),layout='constrained')
    axes[0].plot(range(1,6),np.array(move)/1000,'o-',color='#9d3131')
    axes[0].set(xlabel='Additional seven-iteration pass',ylabel='Maximum horizontal move (km)',xticks=range(1,6),title='Locations do not converge')
    axes[1].plot(range(1,6),rms,'o-',color='#186b95')
    axes[1].set(xlabel='Additional seven-iteration pass',ylabel='Aggregate reported event RMS (s)',xticks=range(1,6),title='Residual reduction does not imply accuracy')
    fig.suptitle('Reproduction diagnostic: rejected alternative-profile calibration',fontsize=11)
    fig.savefig(ROOT/'figures/calibration_convergence_diagnostic.pdf');plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(10,3.5),layout='constrained');tables=[]
    for region,color in [('NW','#176b9a'),('SW','#ad6b21'),('SE','#6d448a')]:
        values=pd.read_csv(D/f'relocation/svd_{region}.csv');values['region']=region;values['cc_count']=values.ncc_p+values.ncc_s;tables.append(values)
        for ax,field in zip(axes,['error_x_m','error_y_m','error_z_m']):
            ax.scatter(values.cc_count,values[field],s=12,c=color,label=f'{region}, n={len(values)}',alpha=.7)
    for ax,title in zip(axes,['Easting','Northing','Depth']):
        ax.set(xlabel='Waveform differential observations',ylabel='Conditional 95% error (m)',title=title)
        ax.set_xscale('symlog',linthresh=1);ax.set_yscale('log');ax.grid(alpha=.2)
    axes[0].legend(fontsize=7);fig.suptitle('Reproduction diagnostic: exploratory SVD; NE diverged; zero counts retained',fontsize=10)
    pd.concat(tables,ignore_index=True).to_csv(D/'svd_diagnostic_plot.csv',index=False)
    fig.savefig(ROOT/'figures/relocation_uncertainty_diagnostic.pdf');plt.close(fig)

if __name__=='__main__':main()
