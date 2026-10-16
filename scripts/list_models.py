"""Print the model IDs available on your Token Factory account (look for Nemotron)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from parallax.llm import get_client

client = get_client()
ids = sorted(m.id for m in client.models.list().data)
nemo = [i for i in ids if "nemotron" in i.lower() or i.lower().startswith("nvidia")]
print("NVIDIA / Nemotron models:")
for i in nemo or ["(none matched - showing all below)"]:
    print("  ", i)
if not nemo:
    for i in ids:
        print("  ", i)
