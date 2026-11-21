import warnings, numpy as np, dimod, sys
warnings.filterwarnings("ignore")
from divi.backends import MaestroSimulator
from divi.qprog.algorithms import QAOA, PCE
from divi.qprog.optimizers import MonteCarloOptimizer
from divi.qprog.problems import BinaryOptimizationProblem
from divi.qprog.algorithms import *
N=6
h={i:(-3.0 if i in (0,1) else 2.0) for i in range(N)}
bqm=dimod.BinaryQuadraticModel(h,{(0,5):0.1},0,dimod.BINARY)
q=QAOA(BinaryOptimizationProblem(bqm),n_layers=2,optimizer=MonteCarloOptimizer(population_size=10),max_iterations=3,backend=MaestroSimulator(shots=2000),seed=1)
q.run(); s=q.get_top_solutions(n=3); print('QAOA',s)
print([a for a in dir(s[0]) if not a.startswith('_')])
try:
    from divi.qprog.algorithms import PolyEncoding, SoftObjective
except Exception as e: print('imp',e)
