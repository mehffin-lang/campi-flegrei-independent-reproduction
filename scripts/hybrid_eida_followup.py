"""Compute candidate measurements for the new continuous-observation scan."""
import grid_hybrid_candidates as h

if __name__=='__main__':
    h.OUT=h.ROOT/'data/eida_continuation/hybrid';h.main()
