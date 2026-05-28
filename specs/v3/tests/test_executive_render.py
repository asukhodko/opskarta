import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from specs.v3.tools.effort import compute_effort_metrics
from specs.v3.tools.execution import compute_execution_metrics
from specs.v3.tools.loader import load_plan_set
from specs.v3.tools.render.executive import render_executive
from specs.v3.tools.render.executive_report import render_executive_report
from specs.v3.tools.scheduler import compute_schedule
from specs.v3.tools.validator import validate


def build_plan(body: str) -> str:
    return textwrap.dedent(body).strip() + "\n"


class ExecutiveRenderTests(unittest.TestCase):
    def load_plan(self, text: str):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "plan.yaml"
            path.write_text(text, encoding="utf-8")
            plan = load_plan_set([str(path)])
            compute_effort_metrics(plan)
            compute_execution_metrics(plan)
            compute_schedule(plan)
            return plan

    def test_render_executive_shows_progress_and_unlabeled_risk_edge(self):
        plan = self.load_plan(
            build_plan(
                """
                version: 3
                nodes:
                  gate-a:
                    title: Gate A
                    kind: milestone
                    milestone: true
                    status: not_started
                  gate-b:
                    title: Gate B
                    kind: milestone
                    milestone: true
                    status: not_started
                  alpha:
                    title: Alpha
                    kind: phase
                    status: in_progress
                  alpha-task:
                    parent: alpha
                    title: Alpha task
                    kind: task
                    status: in_progress
                  beta:
                    title: Beta
                    kind: phase
                    status: not_started
                  beta-task:
                    parent: beta
                    title: Beta task
                    kind: task
                    status: not_started
                schedule:
                  default_calendar: ru
                  calendars:
                    ru:
                      excludes: [weekends]
                  nodes:
                    gate-a:
                      start: "2026-04-10"
                      duration: 1d
                    gate-b:
                      start: "2026-04-20"
                      duration: 1d
                    alpha-task:
                      start: "2026-03-30"
                      duration: 2d
                    beta-task:
                      start: "2026-04-15"
                      duration: 3d
                x:
                  exec:
                    defaults:
                      status_progress:
                        done: 1.0
                        in_progress: 0.5
                        planned: 0.0
                        not_started: 0.0
                        blocked: 0.0
                      weight_strategy: effort_effective
                    blocks:
                      alpha_block:
                        title: Alpha block
                        scope_nodes: [alpha]
                        target_gate: gate-a
                        kind: main
                      beta_block:
                        title: Beta block
                        scope_nodes: [beta]
                        target_gate: gate-b
                        kind: feeder
                      top:
                        title: Top
                        source_blocks: [alpha_block, beta_block]
                        target_gate: gate-b
                        kind: aggregate
                      risk:
                        title: Risk
                        scope_nodes: [beta]
                        target_gate: gate-b
                        kind: risk_sidecar
                    edges:
                      - from: alpha_block
                        to: top
                        type: required
                      - from: beta_block
                        to: top
                        type: required
                      - from: risk
                        to: top
                        type: risk_reduction
                    views:
                      exec-top:
                        direction: LR
                        blocks: [alpha_block, beta_block, top, risk]
                """
            )
        )
        rendered = render_executive(plan, "exec-top")
        self.assertIn('Alpha block<br/>~50%<br/>веха 2026-04-10', rendered)
        self.assertIn('beta_block --> top', rendered)
        self.assertIn('risk -.-> top', rendered)
        self.assertNotIn('снижает риск', rendered)

    def test_render_executive_supports_custom_risk_edge_label(self):
        plan = self.load_plan(
            build_plan(
                """
                version: 3
                nodes:
                  gate-a:
                    title: Gate A
                    kind: milestone
                    milestone: true
                    status: not_started
                  alpha:
                    title: Alpha
                    kind: phase
                    status: in_progress
                  alpha-task:
                    parent: alpha
                    title: Alpha task
                    kind: task
                    status: in_progress
                  risk-phase:
                    title: Risk phase
                    kind: phase
                    status: not_started
                  risk-task:
                    parent: risk-phase
                    title: Risk task
                    kind: task
                    status: not_started
                schedule:
                  default_calendar: ru
                  calendars:
                    ru:
                      excludes: [weekends]
                  nodes:
                    gate-a:
                      start: "2026-04-10"
                      duration: 1d
                    alpha-task:
                      start: "2026-03-30"
                      duration: 2d
                    risk-task:
                      start: "2026-04-15"
                      duration: 1d
                x:
                  exec:
                    blocks:
                      alpha_block:
                        title: Alpha block
                        scope_nodes: [alpha]
                        target_gate: gate-a
                        kind: main
                      risk:
                        title: Risk
                        scope_nodes: [risk-phase]
                        target_gate: gate-a
                        kind: risk_sidecar
                    edges:
                      - from: risk
                        to: alpha_block
                        type: risk_reduction
                        label: снижает риск
                    views:
                      exec-top:
                        direction: LR
                        blocks: [alpha_block, risk]
                """
            )
        )
        rendered = render_executive(plan, "exec-top")
        self.assertIn('risk -. снижает риск .-> alpha_block', rendered)

    def test_progress_override_hides_approximate_prefix(self):
        plan = self.load_plan(
            build_plan(
                """
                version: 3
                nodes:
                  gate:
                    title: Gate
                    kind: milestone
                    milestone: true
                    status: not_started
                  work:
                    title: Work
                    kind: phase
                    status: not_started
                  task:
                    parent: work
                    title: Task
                    kind: task
                    status: not_started
                schedule:
                  default_calendar: ru
                  calendars:
                    ru:
                      excludes: [weekends]
                  nodes:
                    gate:
                      start: "2026-04-10"
                      duration: 1d
                    task:
                      start: "2026-04-01"
                      duration: 2d
                x:
                  exec:
                    blocks:
                      work_block:
                        title: Work block
                        scope_nodes: [work]
                        target_gate: gate
                        kind: main
                        progress_override: 0.25
                    views:
                      exec-top:
                        blocks: [work_block]
                """
            )
        )
        rendered = render_executive(plan, "exec-top")
        self.assertIn('Work block<br/>25%<br/>веха 2026-04-10', rendered)
        self.assertNotIn('~25%', rendered)

    def test_render_executive_uses_window_label_for_date_range(self):
        plan = self.load_plan(
            build_plan(
                """
                version: 3
                nodes:
                  gate-window:
                    title: Gate Window
                    kind: phase
                    status: not_started
                  work:
                    title: Work
                    kind: phase
                    status: not_started
                  task:
                    parent: work
                    title: Task
                    kind: task
                    status: not_started
                schedule:
                  default_calendar: ru
                  calendars:
                    ru:
                      excludes: [weekends]
                  nodes:
                    gate-window:
                      start: "2026-04-21"
                      finish: "2026-04-23"
                    task:
                      start: "2026-04-01"
                      duration: 1d
                x:
                  exec:
                    blocks:
                      work_block:
                        title: Work block
                        scope_nodes: [work]
                        target_gate: gate-window
                        kind: main
                    views:
                      exec-top:
                        blocks: [work_block]
                """
            )
        )
        rendered = render_executive(plan, "exec-top")
        self.assertIn('Work block<br/>~0%<br/>окно 2026-04-21..2026-04-23', rendered)

    def test_render_executive_reduces_transitive_required_edge(self):
        plan = self.load_plan(
            build_plan(
                """
                version: 3
                nodes:
                  gate:
                    title: Gate
                    kind: milestone
                    milestone: true
                    status: not_started
                  alpha:
                    title: Alpha
                    kind: phase
                    status: not_started
                  alpha-task:
                    parent: alpha
                    title: Alpha task
                    kind: task
                    status: not_started
                  beta:
                    title: Beta
                    kind: phase
                    status: not_started
                  beta-task:
                    parent: beta
                    title: Beta task
                    kind: task
                    status: not_started
                  gamma:
                    title: Gamma
                    kind: phase
                    status: not_started
                  gamma-task:
                    parent: gamma
                    title: Gamma task
                    kind: task
                    status: not_started
                schedule:
                  default_calendar: ru
                  calendars:
                    ru:
                      excludes: [weekends]
                  nodes:
                    gate:
                      start: "2026-04-20"
                      duration: 1d
                    alpha-task:
                      start: "2026-04-01"
                      duration: 1d
                    beta-task:
                      start: "2026-04-02"
                      duration: 1d
                    gamma-task:
                      start: "2026-04-03"
                      duration: 1d
                x:
                  exec:
                    blocks:
                      alpha_block:
                        title: Alpha
                        scope_nodes: [alpha]
                        target_gate: gate
                      beta_block:
                        title: Beta
                        scope_nodes: [beta]
                        target_gate: gate
                      gamma_block:
                        title: Gamma
                        scope_nodes: [gamma]
                        target_gate: gate
                    edges:
                      - from: alpha_block
                        to: gamma_block
                        type: required
                      - from: gamma_block
                        to: beta_block
                        type: required
                      - from: alpha_block
                        to: beta_block
                        type: required
                    views:
                      exec-top:
                        blocks: [alpha_block, gamma_block, beta_block]
                """
            )
        )
        rendered = render_executive(plan, "exec-top")
        self.assertIn("alpha_block --> gamma_block", rendered)
        self.assertIn("gamma_block --> beta_block", rendered)
        self.assertNotIn("alpha_block --> beta_block", rendered)

    def test_render_executive_keeps_required_edge_without_transitive_path(self):
        plan = self.load_plan(
            build_plan(
                """
                version: 3
                nodes:
                  gate:
                    title: Gate
                    kind: milestone
                    milestone: true
                    status: not_started
                  alpha:
                    title: Alpha
                    kind: phase
                    status: not_started
                  alpha-task:
                    parent: alpha
                    title: Alpha task
                    kind: task
                    status: not_started
                  beta:
                    title: Beta
                    kind: phase
                    status: not_started
                  beta-task:
                    parent: beta
                    title: Beta task
                    kind: task
                    status: not_started
                  gamma:
                    title: Gamma
                    kind: phase
                    status: not_started
                  gamma-task:
                    parent: gamma
                    title: Gamma task
                    kind: task
                    status: not_started
                schedule:
                  default_calendar: ru
                  calendars:
                    ru:
                      excludes: [weekends]
                  nodes:
                    gate:
                      start: "2026-04-20"
                      duration: 1d
                    alpha-task:
                      start: "2026-04-01"
                      duration: 1d
                    beta-task:
                      start: "2026-04-02"
                      duration: 1d
                    gamma-task:
                      start: "2026-04-03"
                      duration: 1d
                x:
                  exec:
                    blocks:
                      alpha_block:
                        title: Alpha
                        scope_nodes: [alpha]
                        target_gate: gate
                      beta_block:
                        title: Beta
                        scope_nodes: [beta]
                        target_gate: gate
                      gamma_block:
                        title: Gamma
                        scope_nodes: [gamma]
                        target_gate: gate
                    edges:
                      - from: alpha_block
                        to: gamma_block
                        type: required
                      - from: alpha_block
                        to: beta_block
                        type: required
                    views:
                      exec-top:
                        blocks: [alpha_block, gamma_block, beta_block]
                """
            )
        )
        rendered = render_executive(plan, "exec-top")
        self.assertIn("alpha_block --> beta_block", rendered)

    def test_render_executive_context_edge_does_not_reduce_required(self):
        plan = self.load_plan(
            build_plan(
                """
                version: 3
                nodes:
                  gate:
                    title: Gate
                    kind: milestone
                    milestone: true
                    status: not_started
                  alpha:
                    title: Alpha
                    kind: phase
                    status: not_started
                  alpha-task:
                    parent: alpha
                    title: Alpha task
                    kind: task
                    status: not_started
                  beta:
                    title: Beta
                    kind: phase
                    status: not_started
                  beta-task:
                    parent: beta
                    title: Beta task
                    kind: task
                    status: not_started
                  gamma:
                    title: Gamma
                    kind: phase
                    status: not_started
                  gamma-task:
                    parent: gamma
                    title: Gamma task
                    kind: task
                    status: not_started
                schedule:
                  default_calendar: ru
                  calendars:
                    ru:
                      excludes: [weekends]
                  nodes:
                    gate:
                      start: "2026-04-20"
                      duration: 1d
                    alpha-task:
                      start: "2026-04-01"
                      duration: 1d
                    beta-task:
                      start: "2026-04-02"
                      duration: 1d
                    gamma-task:
                      start: "2026-04-03"
                      duration: 1d
                x:
                  exec:
                    blocks:
                      alpha_block:
                        title: Alpha
                        scope_nodes: [alpha]
                        target_gate: gate
                      beta_block:
                        title: Beta
                        scope_nodes: [beta]
                        target_gate: gate
                      gamma_block:
                        title: Gamma
                        scope_nodes: [gamma]
                        target_gate: gate
                    edges:
                      - from: alpha_block
                        to: gamma_block
                        type: required
                      - from: gamma_block
                        to: beta_block
                        type: context
                      - from: alpha_block
                        to: beta_block
                        type: required
                    views:
                      exec-top:
                        blocks: [alpha_block, gamma_block, beta_block]
                """
            )
        )
        rendered = render_executive(plan, "exec-top")
        self.assertIn("alpha_block --> beta_block", rendered)
        self.assertIn("gamma_block -.-> beta_block", rendered)

    def test_render_executive_risk_reduction_edge_does_not_reduce_required(self):
        plan = self.load_plan(
            build_plan(
                """
                version: 3
                nodes:
                  gate:
                    title: Gate
                    kind: milestone
                    milestone: true
                    status: not_started
                  alpha:
                    title: Alpha
                    kind: phase
                    status: not_started
                  alpha-task:
                    parent: alpha
                    title: Alpha task
                    kind: task
                    status: not_started
                  beta:
                    title: Beta
                    kind: phase
                    status: not_started
                  beta-task:
                    parent: beta
                    title: Beta task
                    kind: task
                    status: not_started
                  gamma:
                    title: Gamma
                    kind: phase
                    status: not_started
                  gamma-task:
                    parent: gamma
                    title: Gamma task
                    kind: task
                    status: not_started
                schedule:
                  default_calendar: ru
                  calendars:
                    ru:
                      excludes: [weekends]
                  nodes:
                    gate:
                      start: "2026-04-20"
                      duration: 1d
                    alpha-task:
                      start: "2026-04-01"
                      duration: 1d
                    beta-task:
                      start: "2026-04-02"
                      duration: 1d
                    gamma-task:
                      start: "2026-04-03"
                      duration: 1d
                x:
                  exec:
                    blocks:
                      alpha_block:
                        title: Alpha
                        scope_nodes: [alpha]
                        target_gate: gate
                      beta_block:
                        title: Beta
                        scope_nodes: [beta]
                        target_gate: gate
                      gamma_block:
                        title: Gamma
                        scope_nodes: [gamma]
                        target_gate: gate
                    edges:
                      - from: alpha_block
                        to: gamma_block
                        type: required
                      - from: gamma_block
                        to: beta_block
                        type: risk_reduction
                      - from: alpha_block
                        to: beta_block
                        type: required
                    views:
                      exec-top:
                        blocks: [alpha_block, gamma_block, beta_block]
                """
            )
        )
        rendered = render_executive(plan, "exec-top")
        self.assertIn("alpha_block --> beta_block", rendered)
        self.assertIn("gamma_block -.-> beta_block", rendered)
        self.assertNotIn("снижает риск", rendered)

    def test_render_executive_can_disable_transitive_required_reduction(self):
        plan = self.load_plan(
            build_plan(
                """
                version: 3
                nodes:
                  gate:
                    title: Gate
                    kind: milestone
                    milestone: true
                    status: not_started
                  alpha:
                    title: Alpha
                    kind: phase
                    status: not_started
                  alpha-task:
                    parent: alpha
                    title: Alpha task
                    kind: task
                    status: not_started
                  beta:
                    title: Beta
                    kind: phase
                    status: not_started
                  beta-task:
                    parent: beta
                    title: Beta task
                    kind: task
                    status: not_started
                  gamma:
                    title: Gamma
                    kind: phase
                    status: not_started
                  gamma-task:
                    parent: gamma
                    title: Gamma task
                    kind: task
                    status: not_started
                schedule:
                  default_calendar: ru
                  calendars:
                    ru:
                      excludes: [weekends]
                  nodes:
                    gate:
                      start: "2026-04-20"
                      duration: 1d
                    alpha-task:
                      start: "2026-04-01"
                      duration: 1d
                    beta-task:
                      start: "2026-04-02"
                      duration: 1d
                    gamma-task:
                      start: "2026-04-03"
                      duration: 1d
                x:
                  exec:
                    blocks:
                      alpha_block:
                        title: Alpha
                        scope_nodes: [alpha]
                        target_gate: gate
                      beta_block:
                        title: Beta
                        scope_nodes: [beta]
                        target_gate: gate
                      gamma_block:
                        title: Gamma
                        scope_nodes: [gamma]
                        target_gate: gate
                    edges:
                      - from: alpha_block
                        to: gamma_block
                        type: required
                      - from: gamma_block
                        to: beta_block
                        type: required
                      - from: alpha_block
                        to: beta_block
                        type: required
                    views:
                      exec-top:
                        blocks: [alpha_block, gamma_block, beta_block]
                        reduce_transitive_required_edges: false
                """
            )
        )
        rendered = render_executive(plan, "exec-top")
        self.assertIn("alpha_block --> beta_block", rendered)

    def test_exec_top_can_use_mgmt_hybrid_without_progress(self):
        plan = self.load_plan(
            build_plan(
                """
                version: 3
                nodes:
                  gate-a:
                    title: Gate A
                    kind: milestone
                    milestone: true
                    status: not_started
                  gate-b:
                    title: Gate B
                    kind: milestone
                    milestone: true
                    status: not_started
                  gate-c:
                    title: Gate C
                    kind: milestone
                    milestone: true
                    status: not_started
                  alpha:
                    title: Alpha
                    kind: phase
                    status: in_progress
                  alpha-task:
                    parent: alpha
                    title: Alpha task
                    kind: task
                    status: in_progress
                  beta:
                    title: Beta
                    kind: phase
                    status: not_started
                  beta-task:
                    parent: beta
                    title: Beta task
                    kind: task
                    status: not_started
                  risk-phase:
                    title: Risk phase
                    kind: phase
                    status: in_progress
                  risk-task:
                    parent: risk-phase
                    title: Risk task
                    kind: task
                    status: in_progress
                schedule:
                  default_calendar: ru
                  calendars:
                    ru:
                      excludes: [weekends]
                  nodes:
                    gate-a:
                      start: "2026-04-10"
                      duration: 1d
                    gate-b:
                      start: "2026-04-20"
                      duration: 1d
                    gate-c:
                      start: "2026-04-30"
                      duration: 1d
                    alpha-task:
                      start: "2026-03-30"
                      duration: 2d
                    beta-task:
                      start: "2026-04-15"
                      duration: 3d
                    risk-task:
                      start: "2026-04-05"
                      duration: 2d
                x:
                  exec:
                    blocks:
                      alpha_block:
                        title: Alpha block
                        scope_nodes: [alpha]
                        target_gate: gate-a
                        kind: main
                        mgmt:
                          health: green
                          sync_note: "alpha active"
                      beta_block:
                        title: Beta block
                        scope_nodes: [beta]
                        target_gate: gate-b
                        kind: main
                        mgmt:
                          health: green
                      risk:
                        title: Risk
                        scope_nodes: [risk-phase]
                        target_gate: gate-c
                        kind: risk_sidecar
                        mgmt:
                          health: yellow
                          health_note: "needs attention"
                    edges:
                      - from: alpha_block
                        to: beta_block
                        type: required
                      - from: risk
                        to: beta_block
                        type: risk_reduction
                    views:
                      exec-top:
                        direction: LR
                        color_mode: mgmt_hybrid
                        highlight_current: true
                        show_progress: false
                        blocks: [alpha_block, beta_block, risk]
                """
            )
        )
        rendered = render_executive(plan, "exec-top")
        self.assertIn('Alpha block<br/>веха 2026-04-10', rendered)
        self.assertNotIn('%', rendered)
        self.assertIn('class alpha_block exec_mgmt_green', rendered)
        self.assertIn('style alpha_block stroke:#111827,stroke-width:3px', rendered)
        self.assertIn('class beta_block exec_mgmt_neutral', rendered)
        self.assertIn('class risk exec_mgmt_yellow', rendered)

    def test_exec_top_can_respect_mgmt_health_for_done_block(self):
        plan = self.load_plan(
            build_plan(
                """
                version: 3
                nodes:
                  gate-a:
                    title: Gate A
                    kind: milestone
                    milestone: true
                    status: not_started
                  alpha:
                    title: Alpha
                    kind: phase
                    status: done
                  alpha-task:
                    parent: alpha
                    title: Alpha task
                    kind: task
                    status: done
                schedule:
                  default_calendar: ru
                  calendars:
                    ru:
                      excludes: [weekends]
                  nodes:
                    gate-a:
                      start: "2026-04-10"
                      duration: 1d
                    alpha-task:
                      start: "2026-03-30"
                      duration: 2d
                x:
                  exec:
                    blocks:
                      alpha_block:
                        title: Alpha block
                        scope_nodes: [alpha]
                        target_gate: gate-a
                        kind: main
                        mgmt:
                          health: yellow
                    views:
                      exec-top:
                        direction: LR
                        color_mode: mgmt_hybrid
                        show_progress: false
                        respect_mgmt_health_for_done: true
                        blocks: [alpha_block]
                """
            )
        )
        rendered = render_executive(plan, "exec-top")
        self.assertIn('class alpha_block exec_mgmt_yellow', rendered)
        self.assertNotIn('class alpha_block exec_done', rendered)

    def test_exec_top_highlight_prefers_first_non_green_main_block(self):
        plan = self.load_plan(
            build_plan(
                """
                version: 3
                nodes:
                  gate-a:
                    title: Gate A
                    kind: milestone
                    milestone: true
                    status: not_started
                  gate-b:
                    title: Gate B
                    kind: milestone
                    milestone: true
                    status: not_started
                  metal:
                    title: Metal
                    kind: phase
                    status: in_progress
                  metal-task:
                    parent: metal
                    title: Metal task
                    kind: task
                    status: in_progress
                  prep:
                    title: Prep
                    kind: phase
                    status: in_progress
                  prep-task:
                    parent: prep
                    title: Prep task
                    kind: task
                    status: in_progress
                  risk:
                    title: Risk
                    kind: phase
                    status: in_progress
                  risk-task:
                    parent: risk
                    title: Risk task
                    kind: task
                    status: in_progress
                schedule:
                  default_calendar: ru
                  calendars:
                    ru:
                      excludes: [weekends]
                  nodes:
                    gate-a:
                      start: "2026-04-10"
                      duration: 1d
                    gate-b:
                      start: "2026-04-20"
                      duration: 1d
                    metal-task:
                      start: "2026-03-30"
                      duration: 2d
                    prep-task:
                      start: "2026-03-31"
                      duration: 2d
                    risk-task:
                      start: "2026-04-01"
                      duration: 2d
                x:
                  exec:
                    blocks:
                      metal_block:
                        title: Metal block
                        scope_nodes: [metal]
                        target_gate: gate-a
                        kind: main
                        mgmt:
                          health: green
                      prep_block:
                        title: Prep block
                        scope_nodes: [prep]
                        target_gate: gate-b
                        kind: main
                        mgmt:
                          health: yellow
                      risk_block:
                        title: Risk block
                        scope_nodes: [risk]
                        target_gate: gate-b
                        kind: risk_sidecar
                        mgmt:
                          health: red
                    edges:
                      - from: risk_block
                        to: prep_block
                        type: context
                    views:
                      exec-top:
                        direction: LR
                        color_mode: mgmt_hybrid
                        highlight_current: true
                        show_progress: false
                        blocks: [metal_block, prep_block, risk_block]
                """
            )
        )
        rendered = render_executive(plan, "exec-top")
        self.assertIn('class risk_block exec_mgmt_red', rendered)
        self.assertIn('style prep_block stroke:#111827,stroke-width:3px', rendered)
        self.assertNotIn('style metal_block stroke:#111827,stroke-width:3px', rendered)
        self.assertIn('risk_block -.-> prep_block', rendered)

    def test_exec_view_can_show_owner_in_card_label(self):
        plan = self.load_plan(
            build_plan(
                """
                version: 3
                nodes:
                  gate-a:
                    title: Gate A
                    kind: milestone
                    milestone: true
                    status: not_started
                  alpha:
                    title: Alpha
                    kind: phase
                    status: in_progress
                  alpha-task:
                    parent: alpha
                    title: Alpha task
                    kind: task
                    status: in_progress
                schedule:
                  default_calendar: ru
                  calendars:
                    ru:
                      excludes: [weekends]
                  nodes:
                    gate-a:
                      start: "2026-04-10"
                      duration: 1d
                    alpha-task:
                      start: "2026-03-30"
                      duration: 2d
                x:
                  exec:
                    blocks:
                      alpha_block:
                        title: Alpha block
                        scope_nodes: [alpha]
                        target_gate: gate-a
                        kind: main
                        mgmt:
                          health: green
                          owner: "Артём"
                    views:
                      exec-top:
                        direction: LR
                        color_mode: mgmt_hybrid
                        show_progress: false
                        show_owner: true
                        blocks: [alpha_block]
                """
            )
        )
        rendered = render_executive(plan, "exec-top")
        self.assertIn('Ответственный Артём<br/>Alpha block<br/>веха 2026-04-10', rendered)

    def test_exec_view_keeps_explicit_neutral_mgmt_health_gray(self):
        plan = self.load_plan(
            build_plan(
                """
                version: 3
                nodes:
                  gate-a:
                    title: Gate A
                    kind: milestone
                    milestone: true
                    status: not_started
                  alpha:
                    title: Alpha
                    kind: phase
                    status: in_progress
                  alpha-task:
                    parent: alpha
                    title: Alpha task
                    kind: task
                    status: in_progress
                schedule:
                  default_calendar: ru
                  calendars:
                    ru:
                      excludes: [weekends]
                  nodes:
                    gate-a:
                      start: "2026-04-10"
                      duration: 1d
                    alpha-task:
                      start: "2026-03-30"
                      duration: 2d
                x:
                  exec:
                    blocks:
                      alpha_block:
                        title: Alpha block
                        scope_nodes: [alpha]
                        target_gate: gate-a
                        kind: main
                        mgmt:
                          health: neutral
                          sync_note: "future stage"
                    views:
                      exec-top:
                        direction: LR
                        color_mode: mgmt_hybrid
                        show_progress: false
                        blocks: [alpha_block]
                """
            )
        )
        rendered = render_executive(plan, "exec-top")
        self.assertIn('class alpha_block exec_mgmt_neutral', rendered)

    def test_exec_view_can_wrap_title_and_render_context_edge(self):
        plan = self.load_plan(
            build_plan(
                """
                version: 3
                nodes:
                  gate-a:
                    title: Gate A
                    kind: milestone
                    milestone: true
                    status: not_started
                  current:
                    title: Current
                    kind: phase
                    status: in_progress
                  current-task:
                    parent: current
                    title: Current task
                    kind: task
                    status: in_progress
                  alpha:
                    title: Alpha
                    kind: phase
                    status: in_progress
                  alpha-task:
                    parent: alpha
                    title: Alpha task
                    kind: task
                    status: in_progress
                schedule:
                  default_calendar: ru
                  calendars:
                    ru:
                      excludes: [weekends]
                  nodes:
                    gate-a:
                      start: "2026-04-10"
                      duration: 1d
                    current-task:
                      start: "2026-03-29"
                      duration: 1d
                    alpha-task:
                      start: "2026-03-30"
                      duration: 2d
                x:
                  exec:
                    blocks:
                      current_block:
                        title: Сейчас
                        scope_nodes: [current]
                        kind: risk_sidecar
                      alpha_block:
                        title: Практическая проверка плана и доводка ранбуков
                        scope_nodes: [alpha]
                        target_gate: gate-a
                        kind: main
                        mgmt:
                          health: yellow
                    edges:
                      - from: current_block
                        to: alpha_block
                        type: context
                    views:
                      exec-top:
                        direction: LR
                        color_mode: mgmt_hybrid
                        show_progress: false
                        show_gate_date: false
                        wrap_title_lines: 2
                        blocks: [current_block, alpha_block]
                """
            )
        )
        rendered = render_executive(plan, "exec-top")
        self.assertIn('Практическая проверка<br/>плана и доводка ранбуков', rendered)
        self.assertIn('current_block -.-> alpha_block', rendered)

    def test_exec_view_edges_override_global_edges(self):
        plan = self.load_plan(
            build_plan(
                """
                version: 3
                nodes:
                  gate:
                    title: Gate
                    kind: milestone
                    milestone: true
                    status: not_started
                  alpha:
                    title: Alpha
                    kind: phase
                    status: not_started
                  alpha-task:
                    parent: alpha
                    title: Alpha task
                    kind: task
                    status: not_started
                  beta:
                    title: Beta
                    kind: phase
                    status: not_started
                  beta-task:
                    parent: beta
                    title: Beta task
                    kind: task
                    status: not_started
                  gamma:
                    title: Gamma
                    kind: phase
                    status: not_started
                  gamma-task:
                    parent: gamma
                    title: Gamma task
                    kind: task
                    status: not_started
                schedule:
                  default_calendar: ru
                  calendars:
                    ru:
                      excludes: [weekends]
                  nodes:
                    gate:
                      start: "2026-04-10"
                      duration: 1d
                    alpha-task:
                      start: "2026-04-01"
                      duration: 1d
                    beta-task:
                      start: "2026-04-02"
                      duration: 1d
                    gamma-task:
                      start: "2026-04-03"
                      duration: 1d
                x:
                  exec:
                    blocks:
                      alpha_block:
                        title: Alpha
                        scope_nodes: [alpha]
                        target_gate: gate
                      beta_block:
                        title: Beta
                        scope_nodes: [beta]
                        target_gate: gate
                      gamma_block:
                        title: Gamma
                        scope_nodes: [gamma]
                        target_gate: gate
                    edges:
                      - from: alpha_block
                        to: beta_block
                        type: required
                    views:
                      exec-top:
                        blocks: [alpha_block, beta_block, gamma_block]
                        edges:
                          - from: beta_block
                            to: gamma_block
                            type: context
                            label: локально
                """
            )
        )
        rendered = render_executive(plan, "exec-top")
        self.assertNotIn("alpha_block --> beta_block", rendered)
        self.assertIn("beta_block -. локально .-> gamma_block", rendered)

    def test_validate_rejects_invalid_view_edges(self):
        plan = self.load_plan(
            build_plan(
                """
                version: 3
                nodes:
                  gate:
                    title: Gate
                    kind: milestone
                    milestone: true
                    status: not_started
                  alpha:
                    title: Alpha
                    kind: phase
                    status: not_started
                  alpha-task:
                    parent: alpha
                    title: Alpha task
                    kind: task
                    status: not_started
                  beta:
                    title: Beta
                    kind: phase
                    status: not_started
                  beta-task:
                    parent: beta
                    title: Beta task
                    kind: task
                    status: not_started
                  gamma:
                    title: Gamma
                    kind: phase
                    status: not_started
                  gamma-task:
                    parent: gamma
                    title: Gamma task
                    kind: task
                    status: not_started
                schedule:
                  default_calendar: ru
                  calendars:
                    ru:
                      excludes: [weekends]
                  nodes:
                    gate:
                      start: "2026-04-10"
                      duration: 1d
                    alpha-task:
                      start: "2026-04-01"
                      duration: 1d
                    beta-task:
                      start: "2026-04-02"
                      duration: 1d
                    gamma-task:
                      start: "2026-04-03"
                      duration: 1d
                x:
                  exec:
                    blocks:
                      alpha_block:
                        title: Alpha
                        scope_nodes: [alpha]
                        target_gate: gate
                      beta_block:
                        title: Beta
                        scope_nodes: [beta]
                        target_gate: gate
                      gamma_block:
                        title: Gamma
                        scope_nodes: [gamma]
                        target_gate: gate
                    views:
                      exec-top:
                        blocks: [alpha_block, beta_block]
                        edges:
                          - from: alpha_block
                            to: gamma_block
                            type: strange
                            label: 7
                """
            )
        )
        result = validate(plan)
        self.assertTrue(any("references block outside the view" in e.message for e in result.errors))
        self.assertTrue(any("invalid type" in e.message for e in result.errors))
        self.assertTrue(any("invalid label" in e.message for e in result.errors))

    def test_exec_history_can_render_long_left_tail_and_branching_path(self):
        plan = self.load_plan(
            build_plan(
                """
                version: 3
                nodes:
                  current-gate:
                    title: Current gate
                    kind: milestone
                    milestone: true
                    status: not_started
                  route:
                    title: Route
                    kind: phase
                    status: done
                  route-task:
                    parent: route
                    title: Route task
                    kind: task
                    status: done
                  build-foundation:
                    title: Build foundation
                    kind: phase
                    status: done
                  build-foundation-task:
                    parent: build-foundation
                    title: Build foundation task
                    kind: task
                    status: done
                  ci:
                    title: CI
                    kind: phase
                    status: done
                  ci-task:
                    parent: ci
                    title: CI task
                    kind: task
                    status: done
                  contours:
                    title: Contours
                    kind: phase
                    status: done
                  contours-task:
                    parent: contours
                    title: Contours task
                    kind: task
                    status: done
                  stage:
                    title: Stage
                    kind: phase
                    status: done
                  stage-task:
                    parent: stage
                    title: Stage task
                    kind: task
                    status: done
                  breaking:
                    title: Breaking
                    kind: phase
                    status: done
                  breaking-task:
                    parent: breaking
                    title: Breaking task
                    kind: task
                    status: done
                  front:
                    title: Front
                    kind: phase
                    status: done
                  front-task:
                    parent: front
                    title: Front task
                    kind: task
                    status: done
                  search:
                    title: Search
                    kind: phase
                    status: done
                  search-task:
                    parent: search
                    title: Search task
                    kind: task
                    status: done
                  feature-registry:
                    title: Feature registry
                    kind: phase
                    status: done
                  feature-registry-task:
                    parent: feature-registry
                    title: Feature registry task
                    kind: task
                    status: done
                  uat:
                    title: UAT
                    kind: phase
                    status: done
                  uat-task:
                    parent: uat
                    title: UAT task
                    kind: task
                    status: done
                  metal:
                    title: Metal
                    kind: phase
                    status: done
                  metal-task:
                    parent: metal
                    title: Metal task
                    kind: task
                    status: done
                  full-resync:
                    title: Full resync
                    kind: phase
                    status: done
                  full-resync-task:
                    parent: full-resync
                    title: Full resync task
                    kind: task
                    status: done
                  db-opt:
                    title: DB optimized
                    kind: phase
                    status: done
                  db-opt-task:
                    parent: db-opt
                    title: DB optimized task
                    kind: task
                    status: done
                  prod-services:
                    title: Prod services
                    kind: phase
                    status: done
                  prod-services-task:
                    parent: prod-services
                    title: Prod services task
                    kind: task
                    status: done
                  sre:
                    title: SRE
                    kind: phase
                    status: done
                  sre-task:
                    parent: sre
                    title: SRE task
                    kind: task
                    status: done
                  current:
                    title: Current
                    kind: phase
                    status: in_progress
                  current-task:
                    parent: current
                    title: Current task
                    kind: task
                    status: in_progress
                schedule:
                  default_calendar: ru
                  calendars:
                    ru:
                      excludes: [weekends]
                  nodes:
                    current-gate:
                      start: "2026-04-08"
                      duration: 1d
                    route-task:
                      start: "2025-09-15"
                      duration: 1d
                    build-foundation-task:
                      start: "2025-12-01"
                      duration: 1d
                    ci-task:
                      start: "2025-12-10"
                      duration: 1d
                    contours-task:
                      start: "2026-02-01"
                      duration: 1d
                    stage-task:
                      start: "2026-02-05"
                      duration: 1d
                    breaking-task:
                      start: "2026-02-10"
                      duration: 1d
                    front-task:
                      start: "2026-02-11"
                      duration: 1d
                    search-task:
                      start: "2026-02-12"
                      duration: 1d
                    feature-registry-task:
                      start: "2026-02-16"
                      duration: 1d
                    uat-task:
                      start: "2026-02-18"
                      duration: 1d
                    metal-task:
                      start: "2026-02-20"
                      duration: 1d
                    full-resync-task:
                      start: "2026-02-24"
                      duration: 1d
                    db-opt-task:
                      start: "2026-03-05"
                      duration: 1d
                    prod-services-task:
                      start: "2026-02-15"
                      duration: 1d
                    sre-task:
                      start: "2026-03-10"
                      duration: 1d
                    current-task:
                      start: "2026-03-31"
                      duration: 2d
                x:
                  exec:
                    blocks:
                      history_route:
                        title: Route proven
                        scope_nodes: [route]
                        kind: feeder
                      history_build_foundation:
                        title: Build foundation ready
                        scope_nodes: [build-foundation]
                        kind: feeder
                      history_ci:
                        title: CI ready
                        scope_nodes: [ci]
                        kind: feeder
                      history_contours:
                        title: Contours ready
                        scope_nodes: [contours]
                        kind: feeder
                      history_stage:
                        title: Stage ready
                        scope_nodes: [stage]
                        kind: feeder
                      history_breaking:
                        title: Breaking ready
                        scope_nodes: [breaking]
                        kind: feeder
                      history_front:
                        title: Front ready
                        scope_nodes: [front]
                        kind: feeder
                      history_search:
                        title: Search ready
                        scope_nodes: [search]
                        kind: feeder
                      history_feature_registry:
                        title: Feature registry ready
                        scope_nodes: [feature-registry]
                        kind: feeder
                      history_uat:
                        title: Business validation ready
                        scope_nodes: [uat]
                        kind: feeder
                      history_metal:
                        title: Metal ready
                        scope_nodes: [metal]
                        kind: feeder
                      history_full_resync:
                        title: Full resync ready
                        scope_nodes: [full-resync]
                        kind: feeder
                      history_db_opt:
                        title: DB migration optimized
                        scope_nodes: [db-opt]
                        kind: feeder
                      history_prod_services:
                        title: Prod services ready
                        scope_nodes: [prod-services]
                        kind: feeder
                      history_sre:
                        title: SRE ready
                        scope_nodes: [sre]
                        kind: feeder
                      current_block:
                        title: Current stage
                        scope_nodes: [current]
                        target_gate: current-gate
                        kind: main
                        mgmt:
                          health: green
                    edges:
                      - from: history_route
                        to: history_build_foundation
                        type: required
                      - from: history_build_foundation
                        to: history_contours
                        type: required
                      - from: history_build_foundation
                        to: history_ci
                        type: required
                      - from: history_contours
                        to: history_stage
                        type: required
                      - from: history_stage
                        to: history_breaking
                        type: required
                      - from: history_breaking
                        to: history_front
                        type: required
                      - from: history_contours
                        to: history_search
                        type: required
                      - from: history_contours
                        to: history_feature_registry
                        type: required
                      - from: history_feature_registry
                        to: history_uat
                        type: required
                      - from: history_front
                        to: history_uat
                        type: required
                      - from: history_search
                        to: history_uat
                        type: required
                      - from: history_uat
                        to: current_block
                        type: required
                      - from: history_contours
                        to: history_metal
                        type: required
                      - from: history_metal
                        to: history_full_resync
                        type: required
                      - from: history_full_resync
                        to: history_db_opt
                        type: required
                      - from: history_db_opt
                        to: current_block
                        type: required
                      - from: history_contours
                        to: history_prod_services
                        type: required
                      - from: history_prod_services
                        to: history_sre
                        type: required
                      - from: history_sre
                        to: current_block
                        type: required
                      - from: history_ci
                        to: current_block
                        type: required
                    views:
                      exec-history:
                        direction: LR
                        color_mode: mgmt_hybrid
                        highlight_current: true
                        show_progress: false
                        blocks: [history_route, history_build_foundation, history_ci, history_contours, history_stage, history_breaking, history_front, history_search, history_feature_registry, history_uat, history_metal, history_full_resync, history_db_opt, history_prod_services, history_sre, current_block]
                """
            )
        )
        rendered = render_executive(plan, "exec-history")
        self.assertNotIn("%", rendered)
        self.assertIn('Route proven', rendered)
        self.assertIn("history_route --> history_build_foundation", rendered)
        self.assertIn("history_build_foundation --> history_ci", rendered)
        self.assertIn("history_contours --> history_feature_registry", rendered)
        self.assertIn("history_feature_registry --> history_uat", rendered)
        self.assertIn("history_front --> history_uat", rendered)
        self.assertIn("history_full_resync --> history_db_opt", rendered)
        self.assertIn("history_ci --> current_block", rendered)
        self.assertIn("history_uat --> current_block", rendered)
        self.assertIn("history_sre --> current_block", rendered)
        self.assertIn("CI ready", rendered)
        self.assertIn("Feature registry ready", rendered)
        self.assertIn("Business validation ready", rendered)
        self.assertIn("Metal ready", rendered)
        self.assertIn("Full resync ready", rendered)
        self.assertIn("DB migration optimized", rendered)
        self.assertIn("class history_build_foundation exec_done", rendered)
        self.assertIn("class current_block exec_mgmt_green", rendered)
        self.assertIn("style current_block stroke:#111827,stroke-width:3px", rendered)

    def test_render_executive_report_sections(self):
        plan = self.load_plan(
            build_plan(
                """
                version: 3
                nodes:
                  gate-a:
                    title: Gate A
                    kind: milestone
                    milestone: true
                    status: not_started
                  gate-prod:
                    title: Prod done
                    kind: milestone
                    milestone: true
                    status: not_started
                  alpha:
                    title: Alpha
                    kind: phase
                    status: in_progress
                  alpha-task:
                    parent: alpha
                    title: Alpha task
                    kind: task
                    status: in_progress
                  beta:
                    title: Beta
                    kind: phase
                    status: not_started
                  beta-task:
                    parent: beta
                    title: Beta task
                    kind: task
                    status: not_started
                  gamma:
                    title: Gamma
                    kind: phase
                    status: in_progress
                  gamma-task:
                    parent: gamma
                    title: Gamma task
                    kind: task
                    status: in_progress
                schedule:
                  default_calendar: ru
                  calendars:
                    ru:
                      excludes: [weekends]
                  nodes:
                    gate-a:
                      start: "2026-04-10"
                      duration: 1d
                    gate-prod:
                      start: "2026-05-01"
                      duration: 1d
                    alpha-task:
                      start: "2026-03-30"
                      duration: 2d
                    beta-task:
                      start: "2026-04-15"
                      duration: 3d
                    gamma-task:
                      start: "2026-04-07"
                      duration: 2d
                x:
                  exec:
                    program:
                      committed_date: "2026-04-26"
                      nearest_goal: "Тестовая ближайшая цель"
                      success_by_next_sync: "Тестовый критерий успеха"
                    blocks:
                      alpha_block:
                        title: Alpha block
                        scope_nodes: [alpha]
                        target_gate: gate-a
                        kind: main
                        mgmt:
                          health: green
                          sync_note: "alpha active"
                          next_sync_goal: "finish alpha"
                      beta_block:
                        title: Beta block
                        scope_nodes: [beta]
                        target_gate: gate-prod
                        kind: main
                        mgmt:
                          health: green
                      gamma_block:
                        title: Gamma block
                        scope_nodes: [gamma]
                        target_gate: gate-a
                        kind: feeder
                        mgmt:
                          health: yellow
                          health_note: "yellow signal"
                          blocker_note: "need answer"
                    edges:
                      - from: alpha_block
                        to: beta_block
                        type: required
                    views:
                      exec-top:
                        blocks: [alpha_block, beta_block]
                      exec-active-tracks:
                        blocks: [alpha_block]
                      exec-strategic-tracks:
                        blocks: [gamma_block]
                """
            )
        )
        status = render_executive_report(plan, "status")
        self.assertIn("Обещанная дата", status)
        self.assertIn("`26.04.2026`", status)
        self.assertIn("`01.05.2026`", status)
        self.assertIn("`+5 дней`", status)
        self.assertIn("Ближайшая цель: Тестовая ближайшая цель", status)
        self.assertIn("Что считаем успехом к следующему синку: Тестовый критерий успеха", status)
        self.assertIn("Alpha block", status)

        tracks = render_executive_report(plan, "tracks")
        self.assertIn("### Date-holders", tracks)
        self.assertIn("### Стратегические треки приближения миграции", tracks)
        self.assertIn("| Трек | Состояние |", tracks)
        self.assertIn("| Alpha block | 🟢 |", tracks)
        self.assertIn("| Gamma block | 🟡 |", tracks)
        self.assertIn("alpha active", tracks)
        self.assertIn("finish alpha", tracks)

        signals = render_executive_report(plan, "signals")
        self.assertIn("| Gamma block | 🟡 |", signals)
        self.assertIn("yellow signal", signals)
        self.assertIn("need answer", signals)

    def test_render_executive_report_compacts_multiline_titles_for_markdown(self):
        plan = self.load_plan(
            build_plan(
                """
                version: 3
                nodes:
                  gate:
                    title: Gate
                    kind: milestone
                    milestone: true
                    status: not_started
                  alpha:
                    title: Alpha
                    kind: phase
                    status: in_progress
                  alpha-task:
                    parent: alpha
                    title: Alpha task
                    kind: task
                    status: in_progress
                schedule:
                  default_calendar: ru
                  calendars:
                    ru:
                      excludes: [weekends]
                  nodes:
                    gate:
                      start: "2026-04-10"
                      duration: 1d
                    alpha-task:
                      start: "2026-04-01"
                      duration: 1d
                x:
                  exec:
                    program:
                      committed_date: "2026-04-10"
                    blocks:
                      alpha_block:
                        title: |-
                          Alpha
                          block
                        scope_nodes: [alpha]
                        target_gate: gate
                        kind: main
                        mgmt:
                          health: yellow
                          health_note: |-
                            yellow
                            signal
                          sync_note: |-
                            alpha
                            active
                          next_sync_goal: |-
                            finish
                            alpha
                    views:
                      exec-top:
                        color_mode: mgmt_hybrid
                        blocks: [alpha_block]
                      exec-active-tracks:
                        blocks: [alpha_block]
                """
            )
        )

        status = render_executive_report(plan, "status")
        tracks = render_executive_report(plan, "tracks")
        signals = render_executive_report(plan, "signals")

        self.assertIn("Текущий этап: `Alpha block`", status)
        self.assertIn("| Alpha block | 🟡 |", tracks)
        self.assertIn("alpha active", tracks)
        self.assertIn("finish alpha", tracks)
        self.assertIn("| Alpha block | 🟡 | yellow signal |", signals)
        self.assertNotIn("Alpha\nblock", status + tracks + signals)

    def test_validate_rejects_exec_block_with_both_scope_and_source(self):
        plan = self.load_plan(
            build_plan(
                """
                version: 3
                nodes:
                  gate:
                    title: Gate
                    kind: milestone
                    milestone: true
                    status: not_started
                  alpha:
                    title: Alpha
                    kind: phase
                    status: not_started
                  task:
                    parent: alpha
                    title: Task
                    kind: task
                    status: not_started
                schedule:
                  default_calendar: ru
                  calendars:
                    ru:
                      excludes: [weekends]
                  nodes:
                    gate:
                      start: "2026-04-10"
                      duration: 1d
                    task:
                      start: "2026-04-01"
                      duration: 1d
                x:
                  exec:
                    blocks:
                      broken:
                        title: Broken
                        scope_nodes: [alpha]
                        source_blocks: [broken]
                        target_gate: gate
                    views:
                      exec-top:
                        blocks: [broken]
                """
            )
        )
        result = validate(plan)
        self.assertTrue(any("exactly one of scope_nodes/source_blocks" in e.message for e in result.errors))

    def test_validate_rejects_invalid_mgmt_health(self):
        plan = self.load_plan(
            build_plan(
                """
                version: 3
                nodes:
                  gate:
                    title: Gate
                    kind: milestone
                    milestone: true
                    status: not_started
                  alpha:
                    title: Alpha
                    kind: phase
                    status: not_started
                  task:
                    parent: alpha
                    title: Task
                    kind: task
                    status: not_started
                schedule:
                  default_calendar: ru
                  calendars:
                    ru:
                      excludes: [weekends]
                  nodes:
                    gate:
                      start: "2026-04-10"
                      duration: 1d
                    task:
                      start: "2026-04-01"
                      duration: 1d
                x:
                  exec:
                    program:
                      committed_date: "2026-04-26"
                    blocks:
                      alpha_block:
                        title: Alpha block
                        scope_nodes: [alpha]
                        target_gate: gate
                        kind: main
                        mgmt:
                          health: blue
                    views:
                      exec-top:
                        blocks: [alpha_block]
                      exec-active-tracks:
                        blocks: [alpha_block]
                """
            )
        )
        result = validate(plan)
        self.assertTrue(any("invalid mgmt.health" in e.message for e in result.errors))

    def test_validate_accepts_neutral_mgmt_health(self):
        plan = self.load_plan(
            build_plan(
                """
                version: 3
                nodes:
                  gate:
                    title: Gate
                    kind: milestone
                    milestone: true
                    status: not_started
                  alpha:
                    title: Alpha
                    kind: phase
                    status: not_started
                  task:
                    parent: alpha
                    title: Task
                    kind: task
                    status: not_started
                schedule:
                  default_calendar: ru
                  calendars:
                    ru:
                      excludes: [weekends]
                  nodes:
                    gate:
                      start: "2026-04-10"
                      duration: 1d
                    task:
                      start: "2026-04-01"
                      duration: 1d
                x:
                  exec:
                    program:
                      committed_date: "2026-04-26"
                    blocks:
                      alpha_block:
                        title: Alpha block
                        scope_nodes: [alpha]
                        target_gate: gate
                        kind: main
                        mgmt:
                          health: neutral
                    views:
                      exec-top:
                        blocks: [alpha_block]
                      exec-active-tracks:
                        blocks: [alpha_block]
                """
            )
        )
        result = validate(plan)
        self.assertFalse(any("invalid mgmt.health" in e.message for e in result.errors))


if __name__ == "__main__":
    unittest.main()
