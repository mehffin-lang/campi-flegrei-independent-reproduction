"""Deterministic initialization of permitted generic GaMMA cluster solves.

Upstream seeds each worker, then consumes that worker's random stream across
jobs. Its stream position can therefore depend on scheduling. Reset by the
deterministic DBSCAN label before each solve; do not change data or equations.
This is an explicit implementation choice, not a recovered Tan seed setting.
"""
import numpy as np
import gamma.utils as gamma_utils

BASE_SEED = 42
_original_associate = gamma_utils.associate


def associate_cluster(label, *args, **kwargs):
    np.random.seed((BASE_SEED + int(label)) % (2**32))
    return _original_associate(label, *args, **kwargs)


def install():
    gamma_utils.associate = associate_cluster
