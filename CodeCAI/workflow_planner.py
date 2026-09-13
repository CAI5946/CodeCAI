"""Backward-compatible workflow planner module."""

from CodeCAI.workflow.planner import *  # noqa: F403
from CodeCAI.workflow.planner import main


if __name__ == "__main__":
    raise SystemExit(main())
