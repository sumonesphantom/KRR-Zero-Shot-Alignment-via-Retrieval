"""Smoke test: registry bootstraps the judge pipeline with no stray bare names.

Usage (from repo root):
    python -m api.scripts.smoke_registry
"""

import sys

from api.bootstrap import registry


def main():
    registry.bootstrap()

    stray = [n for n in ("config", "retrieve") if n in sys.modules]
    assert not stray, f"stray bare names: {stray}"

    orch_cls = registry.get_judge_orchestrator_cls()
    assert orch_cls.__name__ == "Orchestrator"

    import inspect
    sig = inspect.signature(orch_cls.run)
    assert "on_event" in sig.parameters, "Orchestrator.run is missing on_event kwarg"

    jcfg = registry.get_judge_config()
    print(f"[smoke] OLLAMA_HOST={jcfg.OLLAMA_HOST}")
    print(f"[smoke] models K={jcfg.KNOWLEDGE_MODEL} S={jcfg.STYLE_MODEL} J={jcfg.JUDGE_MODEL}")
    print(f"[smoke] MAX_REVISIONS={jcfg.MAX_REVISIONS} CONTENT_PRESERVATION_MIN={jcfg.CONTENT_PRESERVATION_MIN}")

    print("[smoke] OK — registry isolates judge pipeline, on_event kwarg present")


if __name__ == "__main__":
    main()
