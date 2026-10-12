# Software verification only

`results/` contains synthetic, analytic and injected-signal fixtures, not empirical results. Build with `g++ -std=c++17 -O3 src/method_checks.cpp -o build/method_checks`; run `build/method_checks config/method_checks.cfg tests/results`, then `.venv/bin/python scripts/check_starting_profile.py` and `.venv/bin/python scripts/validate_association.py`. No plotting or empirical-analysis stage reads these fixtures.

`check_window_reads.py` also writes a software-equivalence record here: it compares direct and cached reads on 60 real observation windows. It creates no earthquake or magnitude result. The empirical pipeline uses unchanged original windows, never an injected signal or a test-output table.
