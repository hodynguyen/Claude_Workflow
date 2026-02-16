"""Tests for workflow state machine (state.py)."""
import json
import os
import sys
import tempfile
import unittest

# Add scripts dir to path
SCRIPTS_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "plugins",
    "hody-workflow",
    "skills",
    "project-profile",
    "scripts",
)
sys.path.insert(0, os.path.abspath(SCRIPTS_DIR))

from state import (
    init_workflow,
    load_state,
    start_agent,
    complete_agent,
    skip_agent,
    complete_workflow,
    abort_workflow,
    get_next_agent,
)


class TestInitWorkflow(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.cwd = self.tmpdir.name
        os.makedirs(os.path.join(self.cwd, ".hody"), exist_ok=True)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_init_workflow(self):
        """Creates state.json with correct structure."""
        phases = {
            "THINK": ["researcher", "architect"],
            "BUILD": ["backend", "frontend"],
            "VERIFY": ["unit-tester", "code-reviewer"],
            "SHIP": ["devops"],
        }
        state = init_workflow(self.cwd, "Add user auth", "new-feature", phases)

        self.assertEqual(state["feature"], "Add user auth")
        self.assertEqual(state["type"], "new-feature")
        self.assertEqual(state["status"], "in_progress")
        self.assertEqual(state["phase_order"], ["THINK", "BUILD", "VERIFY", "SHIP"])
        self.assertEqual(state["phases"]["THINK"]["agents"], ["researcher", "architect"])
        self.assertEqual(state["phases"]["THINK"]["completed"], [])
        self.assertIsNone(state["phases"]["THINK"]["active"])
        self.assertEqual(state["agent_log"], [])
        self.assertIn("created_at", state)
        self.assertIn("updated_at", state)

        # Verify file was written
        path = os.path.join(self.cwd, ".hody", "state.json")
        self.assertTrue(os.path.isfile(path))

    def test_workflow_id_generation(self):
        """ID is generated from feature + date."""
        phases = {"THINK": ["researcher"]}
        state = init_workflow(self.cwd, "Add user auth", "new-feature", phases)
        self.assertTrue(state["workflow_id"].startswith("feat-add-user-auth-"))
        # Contains date portion
        self.assertRegex(state["workflow_id"], r"feat-add-user-auth-\d{8}")

    def test_duplicate_init_overwrites(self):
        """Re-init replaces existing state."""
        phases = {"THINK": ["researcher"]}
        state1 = init_workflow(self.cwd, "Feature A", "new-feature", phases)
        state2 = init_workflow(self.cwd, "Feature B", "bug-fix", phases)
        self.assertEqual(state2["feature"], "Feature B")
        self.assertEqual(state2["type"], "bug-fix")

        loaded = load_state(self.cwd)
        self.assertEqual(loaded["feature"], "Feature B")

    def test_partial_phases(self):
        """Only specified phases are included."""
        phases = {"THINK": ["researcher"], "BUILD": ["backend"]}
        state = init_workflow(self.cwd, "API endpoint", "api-endpoint", phases)
        self.assertEqual(state["phase_order"], ["THINK", "BUILD"])
        self.assertNotIn("VERIFY", state["phases"])


class TestLoadState(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.cwd = self.tmpdir.name

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_load_state_no_file(self):
        """Returns None when no state.json exists."""
        self.assertIsNone(load_state(self.cwd))

    def test_load_state_existing(self):
        """Reads state correctly."""
        phases = {"THINK": ["researcher"]}
        init_workflow(self.cwd, "Test feature", "new-feature", phases)
        state = load_state(self.cwd)
        self.assertIsNotNone(state)
        self.assertEqual(state["feature"], "Test feature")


class TestStartAgent(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.cwd = self.tmpdir.name
        init_workflow(self.cwd, "Test", "new-feature", {
            "THINK": ["researcher", "architect"],
            "BUILD": ["backend"],
        })

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_start_agent(self):
        """Sets active agent and logs start time."""
        state = start_agent(self.cwd, "researcher")
        self.assertEqual(state["phases"]["THINK"]["active"], "researcher")
        self.assertEqual(len(state["agent_log"]), 1)
        self.assertEqual(state["agent_log"][0]["agent"], "researcher")
        self.assertEqual(state["agent_log"][0]["phase"], "THINK")
        self.assertIsNotNone(state["agent_log"][0]["started_at"])
        self.assertIsNone(state["agent_log"][0]["completed_at"])

    def test_start_unknown_agent(self):
        """Raises ValueError for unknown agent."""
        with self.assertRaises(ValueError):
            start_agent(self.cwd, "nonexistent-agent")

    def test_phase_validation_warning(self):
        """Warns if BUILD starts before THINK has progress."""
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            start_agent(self.cwd, "backend")

        output = f.getvalue()
        self.assertIn("Warning", output)
        self.assertIn("THINK", output)


class TestCompleteAgent(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.cwd = self.tmpdir.name
        init_workflow(self.cwd, "Test", "new-feature", {
            "THINK": ["researcher", "architect"],
            "BUILD": ["backend"],
        })
        start_agent(self.cwd, "researcher")

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_complete_agent(self):
        """Marks completed and logs end time."""
        state = complete_agent(self.cwd, "researcher", "Researched OAuth2", ["decisions.md"])
        p = state["phases"]["THINK"]
        self.assertIn("researcher", p["completed"])
        self.assertIsNone(p["active"])

        log = state["agent_log"][0]
        self.assertIsNotNone(log["completed_at"])
        self.assertEqual(log["output_summary"], "Researched OAuth2")
        self.assertEqual(log["kb_files_modified"], ["decisions.md"])

    def test_complete_agent_advances_phase(self):
        """Next agent is in next phase when current phase is done."""
        complete_agent(self.cwd, "researcher")
        start_agent(self.cwd, "architect")
        state = complete_agent(self.cwd, "architect")

        # All THINK agents complete — next should be BUILD
        nxt = get_next_agent(state)
        self.assertEqual(nxt, ("BUILD", "backend"))


class TestSkipAgent(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.cwd = self.tmpdir.name
        init_workflow(self.cwd, "Test", "new-feature", {
            "THINK": ["researcher", "architect"],
            "BUILD": ["backend"],
        })

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_skip_agent(self):
        """Marks agent as skipped."""
        state = skip_agent(self.cwd, "researcher")
        self.assertIn("researcher", state["phases"]["THINK"]["skipped"])
        self.assertNotIn("researcher", state["phases"]["THINK"]["completed"])


class TestGetNextAgent(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.cwd = self.tmpdir.name

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_get_next_agent_first(self):
        """Returns first agent when nothing started."""
        state = init_workflow(self.cwd, "Test", "new-feature", {
            "THINK": ["researcher", "architect"],
            "BUILD": ["backend"],
        })
        nxt = get_next_agent(state)
        self.assertEqual(nxt, ("THINK", "researcher"))

    def test_get_next_agent_mid_workflow(self):
        """Returns correct next agent mid-workflow."""
        init_workflow(self.cwd, "Test", "new-feature", {
            "THINK": ["researcher", "architect"],
            "BUILD": ["backend"],
        })
        start_agent(self.cwd, "researcher")
        state = complete_agent(self.cwd, "researcher")
        nxt = get_next_agent(state)
        self.assertEqual(nxt, ("THINK", "architect"))

    def test_get_next_agent_all_done(self):
        """Returns None when all agents are done."""
        init_workflow(self.cwd, "Test", "new-feature", {
            "THINK": ["researcher"],
        })
        start_agent(self.cwd, "researcher")
        state = complete_agent(self.cwd, "researcher")
        nxt = get_next_agent(state)
        self.assertIsNone(nxt)

    def test_get_next_agent_skipped(self):
        """Skipped agents are skipped in next calculation."""
        init_workflow(self.cwd, "Test", "new-feature", {
            "THINK": ["researcher", "architect"],
            "BUILD": ["backend"],
        })
        skip_agent(self.cwd, "researcher")
        state = load_state(self.cwd)
        nxt = get_next_agent(state)
        self.assertEqual(nxt, ("THINK", "architect"))

    def test_get_next_agent_none_state(self):
        """Returns None for None state."""
        self.assertIsNone(get_next_agent(None))


class TestWorkflowLifecycle(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.cwd = self.tmpdir.name

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_complete_workflow(self):
        """Sets status to completed."""
        init_workflow(self.cwd, "Test", "new-feature", {"THINK": ["researcher"]})
        state = complete_workflow(self.cwd)
        self.assertEqual(state["status"], "completed")

    def test_abort_workflow(self):
        """Sets status to aborted."""
        init_workflow(self.cwd, "Test", "new-feature", {"THINK": ["researcher"]})
        state = abort_workflow(self.cwd)
        self.assertEqual(state["status"], "aborted")

    def test_complete_workflow_no_state(self):
        """Raises error when no state exists."""
        with self.assertRaises(FileNotFoundError):
            complete_workflow(self.cwd)

    def test_full_workflow_lifecycle(self):
        """End-to-end: init → start → complete → next → complete workflow."""
        phases = {
            "THINK": ["researcher"],
            "BUILD": ["backend"],
        }
        init_workflow(self.cwd, "Auth feature", "new-feature", phases)

        # Start and complete researcher
        start_agent(self.cwd, "researcher")
        complete_agent(self.cwd, "researcher", "Done research")

        # Start and complete backend
        start_agent(self.cwd, "backend")
        state = complete_agent(self.cwd, "backend", "Built API")

        # No more agents
        self.assertIsNone(get_next_agent(state))

        # Complete workflow
        state = complete_workflow(self.cwd)
        self.assertEqual(state["status"], "completed")
        self.assertEqual(len(state["agent_log"]), 2)


if __name__ == "__main__":
    unittest.main()
