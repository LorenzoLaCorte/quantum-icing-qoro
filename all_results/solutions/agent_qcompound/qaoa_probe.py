import os, time, resource, warnings, numpy as np, dimod, sys
warnings.filterwarnings("ignore")
sys.path[:0] = [os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if os.path.basename(os.path.dirname(os.path.abspath(__file__))) in ('small', 'net24') else os.path.dirname(os.path.abspath(__file__)), '.']; import memguard; memguard.start()
from divi.backends import MaestroSimulator
from divi.qprog.algorithms import QAOA
from divi.qprog.optimizers import MonteCarloOptimizer
from divi.qprog.problems import BinaryOptimizationProblem
N=int(sys.argv[1]); rng=np.random.default_rng(0)
bqm=dimod.BinaryQuadraticModel({i:rng.normal() for i in range(N)},{(i,j):rng.normal() for i in range(N) for j in range(i+1,N) if rng.random()<0.3},0,dimod.BINARY)
t=time.time()
q=QAOA(BinaryOptimizationProblem(bqm),n_layers=2,optimizer=MonteCarloOptimizer(population_size=20),max_iterations=5,backend=MaestroSimulator(shots=4000),seed=1)
q.run()
sols=q.get_top_solutions(n=20)
print(N,'qubits time',round(time.time()-t,1),'circuits',q.total_circuit_count,'maxrss MB',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss//1024)
print(type(sols[0]), sols[0])
