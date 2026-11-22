# Method

slot-QLNS (quantum-hybrid): same large-neighbourhood search (remove up to 6 units of one period, re-choose 6 log-encoded slots jointly), but the proposals come from Divi PCE (PolyEncoding, 9 qubits for 42 variables, local Maestro simulator, 72k circuits), each polished by exact single/pair unit descent and accepted on the exact multi-period objective (1,500 s from −35,445; code: portfolio_QIcing/formulation/slot_qlns.py).
