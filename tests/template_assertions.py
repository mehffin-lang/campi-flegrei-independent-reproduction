"""Injected signals for software assertions only; never return scientific data."""
import numpy as np

def check_injected_alignment(correlation,template):
    injected=np.zeros(3000);injected[1200:2000]=template
    scores=correlation(injected,template)
    assert np.argmax(scores)==1200 and abs(scores[1200]-1)<1e-10
