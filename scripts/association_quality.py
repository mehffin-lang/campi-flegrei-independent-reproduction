"""Physical consistency flags and observed-waveform review of own associations.

Flags are not an earthquake classifier or the paper's manual review. No routine
catalog, published picks, or synthetic observations enter this calculation.
"""
from pathlib import Path
import os, json, hashlib
ROOT = Path(__file__).resolve().parents[1]
os.environ['MPLCONFIGDIR'] = str(ROOT/'tmp/matplotlib')
import numpy as np
import pandas as pd
from obspy import read, UTCDateTime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
D = ROOT/'data/continuation'


def main():
    events = pd.read_csv(D/'initial_events.csv')
    picks = pd.read_csv(D/'picks.csv')
    assigned = pd.read_csv(D/'associations.csv').merge(picks, left_on='pick_index', right_index=True)
    records = []
    for e in events.to_dict('records'):
        g = assigned[assigned.event_index == e['event_index']]
        travel = np.array([UTCDateTime(t)-UTCDateTime(e['time']) for t in g.time])
        bad_sp = 0
        for _, station in g.groupby('trace_id'):
            p, s = station[station.phase == 'P'], station[station.phase == 'S']
            if len(p) == len(s) == 1:
                bad_sp += UTCDateTime(s.time.iloc[0]) <= UTCDateTime(p.time.iloc[0])
        records.append(dict(event_index=e['event_index'], time=e['time'],
            p_picks=int((g.phase == 'P').sum()), s_picks=int((g.phase == 'S').sum()),
            stations=g.trace_id.nunique(), picks=len(g), nonpositive_travel_times=int((travel <= 0).sum()),
            nonpositive_sp_pairs=int(bad_sp), initial_depth_km=e['z(km)'],
            depth_boundary=bool(e['z(km)'] <= 1e-6 or e['z(km)'] >= 8-1e-6),
            passes_causality=bool((travel > 0).all() and bad_sp == 0)))
    q = pd.DataFrame(records)
    q.to_csv(D/'association_quality.csv', index=False)
    # Select a few reproducible inspection examples by failure category, not by
    # a released earthquake list or an attempt to improve published agreement.
    selectors = [('S-only', q.p_picks == 0), ('nonpositive S-P', q.nonpositive_sp_pairs > 0),
                 ('lower depth bound', q.initial_depth_km <= 1e-6),
                 ('upper depth bound', q.initial_depth_km >= 8-1e-6),
                 ('most picks, passes causality', q.passes_causality & ~q.depth_boundary & (q.p_picks > 0))]
    selected = []
    for category, mask in selectors:
        pool = q[mask & ~q.event_index.isin([r['event_index'] for r in selected])]
        if len(pool):
            row = pool.sort_values(['picks','event_index'], ascending=[False, True]).iloc[0]
            selected.append(dict(event_index=int(row.event_index), category=category))
    review = D/'association_review'
    review.mkdir(exist_ok=True)
    # This directory is owned by this script; baseline review has a separate
    # frozen copy under data/resumption. Do not leave orphaned current examples.
    for old in list(review.glob('event_*.npz'))+list(review.glob('event_*_picks.csv')):old.unlink()
    receipt = []
    with PdfPages(ROOT/'figures/association_review_diagnostic.pdf') as pdf:
        for item in selected:
            eid = item['event_index']; e = events[events.event_index == eid].iloc[0]
            origin = UTCDateTime(e.time); g = assigned[assigned.event_index == eid]
            arrays = {}; traces = []; errors = []
            for ident, group in g.groupby('trace_id'):
                # Use the source carrying this station's own assigned phase.
                source = group.sort_values('time').source.iloc[0]
                try:
                    net, sta, loc = ident.split('.')
                    st = read(str(ROOT/source), starttime=origin-2, endtime=origin+14)
                    st = st.select(network=net, station=sta, location=loc).merge(method=0).split()
                    for tr in st:
                        tr.detrend('demean')
                        # Display filter only: no result is accepted/rejected by it.
                        tr.filter('highpass', freq=1, corners=4, zerophase=False)
                        scale = float(np.max(np.abs(tr.data)))
                        if not scale: continue
                        key = 'trace_'+str(len(traces))
                        arrays[key] = np.vstack([tr.times(reftime=origin), tr.data/scale])
                        traces.append(dict(key=key, trace_id=ident, channel=tr.id,
                                           source=source, normalizer_counts=scale))
                except Exception as exc:
                    errors.append(dict(station=ident, error=repr(exc)))
            np.savez_compressed(review/f'event_{eid}.npz', **arrays)
            phasefile = review/f'event_{eid}_picks.csv'
            g.assign(seconds_from_origin=[UTCDateTime(t)-origin for t in g.time]).to_csv(phasefile, index=False)
            saved = np.load(review/f'event_{eid}.npz'); phases = pd.read_csv(phasefile)
            identifiers = sorted({r['trace_id'] for r in traces})
            fig, ax = plt.subplots(figsize=(11, max(5, .42*len(identifiers)+2)))
            for i, ident in enumerate(identifiers):
                for r in [r for r in traces if r['trace_id'] == ident]:
                    x, y = saved[r['key']]
                    component = r['channel'][-1]
                    ax.plot(x, i+.35*y, color={'Z':'black','N':'#5293ba','E':'#b2b2b2'}.get(component,'#888888'), lw=.4)
                for r in phases[phases.trace_id == ident].itertuples():
                    ax.plot([r.seconds_from_origin]*2, [i-.4,i+.4], color='#c63737' if r.phase == 'P' else '#25a035', lw=1)
            ax.set(yticks=range(len(identifiers)), yticklabels=identifiers, xlim=(-2,14),
                   xlabel='Seconds from provisional origin (UTC '+str(origin)+')',
                   title=f'Reproduction diagnostic: event {eid}; {item["category"]}\nObserved 1-Hz-highpass traces, separately normalized; red P, green S; unvalidated locations')
            ax.tick_params(labelsize=8); fig.tight_layout(); pdf.savefig(fig); plt.close(fig)
            receipt.append(dict(**item, input_files=sorted({r['source'] for r in traces}), traces=traces, errors=errors,
                                data=str((review/f'event_{eid}.npz').relative_to(ROOT)),
                                review_status='Waveform inspection examples; no automatic acceptance or manual ground-truth labels'))
    summary = dict(events=len(q), s_only=int((q.p_picks == 0).sum()),
        at_depth_bounds=int(q.depth_boundary.sum()), events_nonpositive_sp=int((q.nonpositive_sp_pairs > 0).sum()),
        events_nonpositive_travel=int((q.nonpositive_travel_times > 0).sum()),
        passes_causality=int(q.passes_causality.sum()), reviewed_examples=receipt,
        input_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [D/'picks.csv',D/'associations.csv',D/'initial_events.csv']},
        interpretation='Necessary causality checks only; passing them does not validate an earthquake, depth or magnitude. No picks, associations or scientific selection were changed. Review examples are not the published S4/S12 panels.')
    (D/'association_quality.json').write_text(json.dumps(summary, indent=2)+'\n')
    print({k:v for k,v in summary.items() if k not in ['reviewed_examples','input_hashes']})


if __name__ == '__main__': main()
