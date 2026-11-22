
import json
from pathlib import Path
import aqora

# ====================================
# EDIT THESE THREE VALUES
# ====================================

name = "network18"
qubits = 18
method = "classical + quantum (more info later)"

# ====================================
# UPLOAD TO AQORA STORE
# ====================================

sol_file = Path(f"{name}.sol")

if not sol_file.is_file():
    raise FileNotFoundError(f"Missing solution: {sol_file}")

store = aqora.Store()

# Upload .sol
sol_key = f"pushquantum-2026-qoro/{name}.sol"
sol_data = sol_file.read_bytes()

store.put(sol_key, sol_data)
print(f"Uploaded: {sol_key}")

# Upload metadata .json
json_key = f"pushquantum-2026-qoro/{name}.json"

metadata = {
    "qubits": qubits,
    "method": method
}

json_data = json.dumps(metadata).encode("utf-8")

store.put(
    json_key,
    json_data,
    content_type="application/json"
)

print(f"Uploaded: {json_key}")

# ====================================
# VERIFY UPLOAD
# ====================================

assert store.get(sol_key) == sol_data
assert store.get(json_key) == json_data

print("\nSUCCESS: Both files uploaded and verified!")
print("Solution:", sol_key)
print("Metadata:", metadata)
