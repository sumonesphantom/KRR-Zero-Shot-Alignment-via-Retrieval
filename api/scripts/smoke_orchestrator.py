"""End-to-end smoke: registry → Orchestrator.run with on_event callback → events.

Requires:
  - FAISS index built (`python previous/run_pipeline.py --step index`)
  - Ollama reachable with the configured model pulled

Usage:
  python -m api.scripts.smoke_orchestrator \
      "be formal and academic" "Explain how a computer stores data."
"""

import sys

from api.bootstrap import registry


def main(preference: str, query: str):
    registry.bootstrap(load_previous=False)
    Orchestrator = registry.get_judge_orchestrator_cls()
    orch = Orchestrator()

    events = []

    def on_event(ev: dict):
        events.append(ev)
        t = ev.get("type")
        print(f"[event] {t}  keys={list(ev)}")

    trace = orch.run(query, preference, top_k=3, on_event=on_event)
    print("\n=== final ===")
    print(f"style_id: {trace.final_style_id}")
    print(f"verdict : {trace.final_verdict}")
    print(f"output  : {trace.final_output[:200]}")
    print(f"\nevent count: {len(events)}")
    assert any(e["type"] == "retrieval" for e in events)
    assert any(e["type"] == "draft" for e in events)
    assert any(e["type"] == "style_attempt" for e in events)
    assert any(e["type"] == "judge_verdict" for e in events)
    assert any(e["type"] == "final" for e in events)
    print("[smoke] OK")


if __name__ == "__main__":
    pref = sys.argv[1] if len(sys.argv) > 1 else "be formal and academic"
    q = sys.argv[2] if len(sys.argv) > 2 else "Explain how a computer stores data."
    main(pref, q)
