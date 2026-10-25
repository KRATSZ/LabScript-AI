"""Isolated newer Flex (OT-3) protocol/runtime namespace.

This package is intentionally separate from the legacy ``sim.flex_*`` modules.
It can be copied into LabScript-AI's Flex runtime without changing the OT-2
helpers or the shared web player.  The public handoff is:

* :func:`flex_protocol.load_analysis` → :func:`flex_protocol.plan`
* :func:`flex_protocol.scene_spec`
* :func:`flex_scene.write_model`
* :class:`play_protocol.Scene` for MuJoCo frame application/checks
"""

from .flex_protocol import load_analysis, plan, scene_spec
from .flex_scene import load_deck, load_model, write_model

__all__ = [
    "load_analysis",
    "plan",
    "scene_spec",
    "load_deck",
    "load_model",
    "write_model",
]
