"""Visual style for observed routine-catalog panels 1A and S5.

Published figures were viewed, not sampled or digitized. No published image
is read here. Numerical inputs remain the separately selected routine CSVs.
Magnitude controls circle area; depth controls color. The original area law
is not specified: the explicit exponential law below is a display assumption.
"""
import hashlib
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.ticker import MultipleLocator

MAP_LIMITS={'1A':((-7,5),(-5,5)), 'S5':((-5.8,3.5),(-3.5,3.5))}


def areas(magnitude):
    # A positive display offset keeps small events visible; magnitudes are
    # unchanged and the area mapping remains strictly increasing.
    return .7+3.*10.**(np.asarray(magnitude,float)-2.)


def frame(ax,grid=False):
    ax.set_facecolor('black')
    ax.tick_params(colors='white',direction='out',length=3,width=.6)
    for spine in ax.spines.values():
        spine.set_visible(True);spine.set_color('.8');spine.set_linewidth(.6)
    for label in [ax.xaxis.label,ax.yaxis.label,ax.title]:
        label.set_color('white');label.set_family('DejaVu Serif')
    for tick in ax.get_xticklabels()+ax.get_yticklabels():
        tick.set_family('DejaVu Serif')
    ax.set_axisbelow(True)
    if grid:ax.grid(color='white',alpha=.3,linewidth=.55)


def points(ax,cat,x,y,norm):
    known=cat.Md.notna()
    # Missing magnitudes have an explicitly distinct, fixed-size symbol.
    d=cat.loc[known].sort_values('Md')
    ax.scatter(d[x],d[y],c=d.depth_km,s=areas(d.Md),cmap='jet_r',norm=norm,
               alpha=.75,linewidths=0,rasterized=True,zorder=2)
    d=cat.loc[~known]
    if len(d):ax.scatter(d[x],d[y],c=d.depth_km,s=2,marker='x',cmap='jet_r',norm=norm,
                         alpha=.65,linewidths=.35,rasterized=True,zorder=2)


def size_key(ax,stars=False,location='upper left'):
    handles=[]
    if stars:handles.append(ax.scatter([],[],marker='*',s=95,color='#ed271c',label=r'$M_d\geq4.0$'))
    for m in [2,3,4]:
        handles.append(ax.scatter([],[],s=areas(m),c='.7',edgecolor='.85',lw=.5,label=rf'$M_d={m:.1f}$'))
    handles.append(ax.scatter([],[],s=8,marker='x',c='.7',linewidths=.5,label=r'$M_d$ unavailable'))
    legend=ax.legend(handles=handles,loc=location,facecolor='black',edgecolor='none',labelcolor='white',
                     framealpha=.85,fontsize=8,labelspacing=.6,borderpad=.7)
    for text in legend.get_texts():text.set_family('DejaVu Serif')


def map_panel(ax,cat,panel,coast,title):
    depth_max=float(np.ceil(cat.depth_km.max()))
    norm=Normalize(vmin=0,vmax=depth_max)
    coast(ax)
    for line in ax.lines:line.set_color('white');line.set_linewidth(.5)
    points(ax,cat,'x_km','y_km',norm)
    limits=MAP_LIMITS[panel]
    ax.set(xlim=limits[0],ylim=limits[1],xlabel='Easting (km)',ylabel='Northing (km)',title=title,aspect='equal')
    ax.xaxis.set_major_locator(MultipleLocator(2 if panel=='1A' else 1))
    ax.yaxis.set_major_locator(MultipleLocator(2 if panel=='1A' else 1))
    frame(ax,grid=panel=='S5')
    if panel=='1A':
        d=cat[cat.Md>=4]
        ax.scatter(d.x_km,d.y_km,marker='*',s=95,color='#ed271c',edgecolors='#b80d0d',lw=.5,zorder=3)
    size_key(ax,stars=panel=='1A',location='upper left' if panel=='1A' else 'lower left')
    outside=(~(cat.x_km.between(*limits[0])&cat.y_km.between(*limits[1]))).sum()
    if panel=='1A':
        ax.text(.02,.02,f'{outside} events outside view; retained in table',transform=ax.transAxes,color='white',fontsize=6,
                bbox=dict(facecolor='black',edgecolor='none',alpha=.8,pad=2),va='bottom')
    return ScalarMappable(norm=norm,cmap='jet_r')


def depth_bar(fig,ax,mappable,vertical=False):
    cb=fig.colorbar(mappable,ax=ax,orientation='vertical' if vertical else 'horizontal',
                    fraction=.07 if vertical else .045,pad=.06,aspect=22)
    top=mappable.norm.vmax
    cb.set_ticks(np.arange(0,top+1,1 if top<=6 else 2))
    cb.set_label(f'Depth (km); scale extended to {top:g} km',color='white',family='DejaVu Serif',fontsize=9)
    cb.ax.tick_params(colors='white',labelsize=8,length=3,width=.6);cb.outline.set_edgecolor('.8')
    if vertical:cb.ax.invert_yaxis()
    return cb


def standalone(root,coast):
    data=root/'data/continuation';figures=root/'figures';scopes=[];record={}
    for panel,filename in [('1A','figure_1A.csv'),('S5','figure_S5.csv')]:
        cat=pd.read_csv(data/filename);lim=MAP_LIMITS[panel];maximum=float(np.ceil(cat.depth_km.max()))
        fig=plt.figure(figsize=(7.1,6.7) if panel=='1A' else (10,8.8),facecolor='black',layout='constrained')
        if panel=='1A':
            ax=fig.subplots();sm=map_panel(ax,cat,panel,coast,'A · Routine-catalog data, 2005–20 March 2025')
            depth_bar(fig,ax,sm);target='figure_1A_routine.pdf'
            views=[('1A','x_km','y_km',lim[0],lim[1])]
        else:
            grid=fig.add_gridspec(2,2,width_ratios=[lim[0][1]-lim[0][0],maximum],height_ratios=[7,maximum])
            ax=fig.add_subplot(grid[0,0]);b=fig.add_subplot(grid[0,1]);c=fig.add_subplot(grid[1,0]);key=fig.add_subplot(grid[1,1]);key.axis('off')
            sm=map_panel(ax,cat,panel,coast,'S5 · Routine-catalog data')
            points(b,cat,'depth_km','y_km',sm.norm);b.set(xlim=(0,maximum),ylim=lim[1],xlabel='Depth (km)',aspect='equal')
            b.xaxis.tick_top();b.xaxis.set_major_locator(MultipleLocator(1));b.yaxis.set_major_locator(MultipleLocator(1));frame(b,grid=True)
            points(c,cat,'x_km','depth_km',sm.norm);c.set(xlim=lim[0],ylim=(maximum,0),xlabel='Easting (km)',ylabel='Depth (km)',aspect='equal')
            c.xaxis.set_major_locator(MultipleLocator(1));c.yaxis.set_major_locator(MultipleLocator(1));frame(c,grid=True)
            depth_bar(fig,key,sm,vertical=True)
            views=[('S5/map','x_km','y_km',lim[0],lim[1]),('S5/northing-depth','depth_km','y_km',(0,maximum),lim[1]),('S5/easting-depth','x_km','depth_km',lim[0],(0,maximum))]
            counts=[]
            for name,x,y,xlim,ylim in views:
                counts.append(int((~(cat[x].between(*xlim)&cat[y].between(*ylim))).sum()))
            key.text(.03,.95,f'{len(cat):,} located routine events\n21 Jan 2022–20 Mar 2025\nSnapshot: 12 Oct 2026\n\nExternal routine catalog;\nnot independent detections.\n\nOutside map / side / bottom:\n{counts[0]} / {counts[1]} / {counts[2]}\nAll retained in source table.\n\nRelief not reconstructed.\nDepth relative to sea level.',
                     transform=key.transAxes,color='white',fontsize=9,va='top',linespacing=1.5)
            target='figure_S5_routine.pdf'
        fig.savefig(figures/target,facecolor=fig.get_facecolor(),dpi=200);plt.close(fig)
        for name,x,y,xlim,ylim in views:
            inside=cat[x].between(*xlim)&cat[y].between(*ylim)
            scopes.append(dict(panel=name,saved_input='data/continuation/'+filename,selected_events=len(cat),in_view=int(inside.sum()),outside_view=int((~inside).sum()),first_axis=x,first_min=xlim[0],first_max=xlim[1],second_axis=y,second_min=ylim[0],second_max=ylim[1],units='km',role='Display extent only; excluded points remain in the selected numerical table'))
        record[panel]=dict(input='data/continuation/'+filename,sha256=hashlib.sha256((data/filename).read_bytes()).hexdigest(),events=len(cat),missing_magnitude=int(cat.Md.isna().sum()),
            depth_range_km=[float(cat.depth_km.min()),float(cat.depth_km.max())],color_limits_km=[0,maximum],palette='jet_r',
            circle_area_points_squared='0.7 + 3 * 10**(Md - 2); points squared; additive visibility offset; exact publication law unspecified; no clipping',missing_magnitude_symbol='fixed-size cross colored by observed depth',
            status='Partial reconstruction from external routine catalog, not independent detections',output='figures/'+target)
    pd.DataFrame(scopes).to_csv(data/'routine_plot_scope.csv',index=False)
    record['reference_use']='Published 1A and S5 viewed only for aesthetics. No image or author numerical result read by plotting code; no relief or geographic features inferred from pixels.'
    record['unavailable']='Figure 3 and 4A–B have no accepted independent data; no new counterpart or stylistic placeholder generated.'
    (data/'routine_plot_style.json').write_text(json.dumps(record,indent=2)+'\n')
