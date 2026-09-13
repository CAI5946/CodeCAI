from __future__ import annotations

import unittest

from CodeCAI.workflow import WorkflowPlan, build_inspect_handoff_workflow_plan
from CodeCAI.workflow.clarify import DEFAULT_MAX_CLARIFY_ROUNDS
from CodeCAI.workflow.commands import handle_workflow_command
from CodeCAI.workflow.planner import compile_workflow
from CodeCAI.workflow.runner import SerialWorkflowRunner


class WorkflowPackageTests(unittest.TestCase):
    def test_workflow_package_exports_old_public_api_and_new_submodules(self) -> None:
        plan = build_inspect_handoff_workflow_plan()

        self.assertIsInstance(plan, WorkflowPlan)
        self.assertEqual("inspect_handoff", compile_workflow("Read README").spec.name)
        self.assertEqual(DEFAULT_MAX_CLARIFY_ROUNDS, 8)
        self.assertIsNotNone(handle_workflow_command)
        self.assertIsNotNone(SerialWorkflowRunner)


if __name__ == "__main__":
    unittest.main()
