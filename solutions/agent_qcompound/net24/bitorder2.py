import warnings, numpy as np, dimod, sys, time
warnings.filterwarnings("ignore")
from divi.backends import MaestroSimulator
from divi.qprog.algorithms import PCE, PolyEncoding, SoftObjective
from divi.qprog.optimizers import MonteCarloOptimizer
from divi.qprog.problems import BinaryOptimizationProblem
N=40
h={i:(-3.0 if i in (0,1,7) else 2.0) for i in range(N)}
bqm=dimod.BinaryQuadraticModel(h,{(0,5):0.1},0,dimod.BINARY)
t=time.time()
p=PCE(BinaryOptimizationProblem(bqm),encoding=PolyEncoding(),objective=SoftObjective(alpha=2.0),n_layers=2,optimizer=MonteCarloOptimizer(population_size=20),max_iterations=10,backend=MaestroSimulator(shots=4000),seed=1)
p.run(); s=p.get_top_solutions(n=5,min_prob=0.0,sort_by="energy"); print('PCE',time.time()-t, p.total_circuit_count)
for e in s: print(e.bitstring, e.decoded, e.energy, e.prob)
import resource; print('rss',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss//1024)
