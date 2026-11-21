import warnings, numpy as np, dimod; warnings.filterwarnings("ignore")
from divi.backends import MaestroSimulator
from divi.qprog.algorithms import QAOA
from divi.qprog.optimizers import MonteCarloOptimizer
from divi.qprog.problems import BinaryOptimizationProblem
N=8; S={0,1,5}
bqm=dimod.BinaryQuadraticModel({i:(-1.0 if i in S else 1.0) for i in range(N)},{},0,dimod.BINARY)
q=QAOA(BinaryOptimizationProblem(bqm),n_layers=2,optimizer=MonteCarloOptimizer(population_size=10),max_iterations=4,backend=MaestroSimulator(shots=2000),seed=1)
q.run()
for s in q.get_top_solutions(n=5, include_decoded=True): print(s)
print(bqm.variables)
