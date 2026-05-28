from __future__ import annotations

from datetime import date
from typing import Optional

from specs.v3.tools.models import MergedPlan
from specs.v3.tools.render.executive import (
    BlockSnapshot,
    ExecConfigError,
    _block_mgmt,
    _build_snapshot,
    _current_main_block_id,
    _exec_cfg,
    _exec_views,
)

HEALTH_BADGES = {
    "green": "🟢",
    "yellow": "🟡",
    "red": "🔴",
    "neutral": "⚪",
}


def _compact_text(value: object) -> str:
    return " ".join(str(value).splitlines())


def _table_cell(value: object) -> str:
    return _compact_text(value).replace("|", "\\|")


def _parse_iso_date(value: str | None) -> Optional[date]:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _format_date(value: str | None) -> str:
    parsed = _parse_iso_date(value)
    if parsed is None:
        return value or "—"
    return parsed.strftime("%d.%m.%Y")


def _view_snapshots(plan: MergedPlan, view_id: str) -> tuple[list[str], dict[str, BlockSnapshot]]:
    view = _exec_views(plan).get(view_id)
    if not isinstance(view, dict):
        raise ExecConfigError(f"Executive view '{view_id}' не найден")
    block_ids = view.get("blocks")
    if not isinstance(block_ids, list) or not all(isinstance(v, str) for v in block_ids):
        raise ExecConfigError(f"Executive view '{view_id}' должен содержать blocks: list[string]")
    cache: dict[str, BlockSnapshot] = {}
    snapshots = {block_id: _build_snapshot(plan, block_id, cache) for block_id in block_ids}
    return block_ids, snapshots


def _gate_text(plan: MergedPlan, snapshot: BlockSnapshot) -> str:
    if not snapshot.target_gate:
        return "—"
    gate = plan.nodes.get(snapshot.target_gate)
    gate_title = _compact_text(gate.title if gate and gate.title else snapshot.target_gate)
    return f"{_format_date(snapshot.gate_date_text)} — {gate_title}"


def _signal_label(health: str, blocker_note: str) -> str:
    if health in HEALTH_BADGES:
        return HEALTH_BADGES[health]
    if blocker_note:
        return "🔗"
    return health or "—"


def _health_badge(health: str) -> str:
    return HEALTH_BADGES.get(health, health or "—")


def _signal_detail(mgmt: dict[str, str]) -> str:
    parts: list[str] = []
    if mgmt.get("health_note"):
        parts.append(mgmt["health_note"])
    if mgmt.get("blocker_note"):
        parts.append(f"Зависимость: {mgmt['blocker_note']}")
    return " ".join(parts) or "—"


def _track_rows(
    plan: MergedPlan,
    block_ids: list[str],
    snapshots: dict[str, BlockSnapshot],
    blocks: dict[str, object],
) -> list[str]:
    rows: list[str] = []
    for block_id in block_ids:
        block = blocks.get(block_id, {})
        mgmt = _block_mgmt(block if isinstance(block, dict) else {})
        snapshot = snapshots[block_id]
        rows.append(
            "| {title} | {health} | {gate} | {sync} | {goal} |".format(
                title=_table_cell(snapshot.title),
                health=_health_badge(mgmt.get("health") or ""),
                gate=_table_cell(_gate_text(plan, snapshot)),
                sync=_table_cell(mgmt.get("sync_note") or "—"),
                goal=_table_cell(mgmt.get("next_sync_goal") or "—"),
            )
        )
    return rows


def _track_table(
    plan: MergedPlan,
    block_ids: list[str],
    snapshots: dict[str, BlockSnapshot],
    blocks: dict[str, object],
) -> str:
    lines = [
        "| Трек | Состояние | Ближайшая веха | Что сейчас происходит | Что должно сдвинуться к следующему синку |",
        "|---|---|---|---|---|",
        *_track_rows(plan, block_ids, snapshots, blocks),
    ]
    return "\n".join(lines)


def _signal_rows(
    plan: MergedPlan,
    block_ids: list[str],
    snapshots: dict[str, BlockSnapshot],
    blocks: dict[str, object],
) -> list[str]:
    rows: list[str] = []
    for block_id in block_ids:
        block = blocks.get(block_id, {})
        mgmt = _block_mgmt(block if isinstance(block, dict) else {})
        health = mgmt.get("health", "")
        blocker_note = mgmt.get("blocker_note", "")
        if health in {"green", "neutral"} and not blocker_note:
            continue
        snapshot = snapshots[block_id]
        rows.append(
            "| {title} | {signal} | {detail} | {gate} |".format(
                title=_table_cell(snapshot.title),
                signal=_signal_label(health, blocker_note),
                detail=_table_cell(_signal_detail(mgmt)),
                gate=_table_cell(_gate_text(plan, snapshot)),
            )
        )
    return rows


def render_executive_report(plan: MergedPlan, section: str) -> str:
    exec_cfg = _exec_cfg(plan)
    program = exec_cfg.get("program") if isinstance(exec_cfg.get("program"), dict) else {}

    if section == "status":
        top_ids, top_snapshots = _view_snapshots(plan, "exec-top")
        top_view = _exec_views(plan).get("exec-top") if isinstance(_exec_views(plan), dict) else {}
        color_mode = str(top_view.get("color_mode") or "status") if isinstance(top_view, dict) else "status"
        blocks = exec_cfg.get("blocks", {}) if isinstance(exec_cfg.get("blocks"), dict) else {}
        current_block_id = _current_main_block_id(top_ids, top_snapshots, blocks, color_mode=color_mode)
        committed_date = program.get("committed_date") if isinstance(program.get("committed_date"), str) else None

        prod_gate_date = None
        if "prod" in top_snapshots:
            prod_gate_date = top_snapshots["prod"].gate_date_text
        else:
            for block_id in reversed(top_ids):
                snapshot = top_snapshots[block_id]
                if snapshot.kind == "risk_sidecar":
                    continue
                if snapshot.target_gate:
                    prod_gate_date = snapshot.gate_date_text
                    break

        committed = _parse_iso_date(committed_date)
        forecast = _parse_iso_date(prod_gate_date)
        if committed and forecast:
            delta_days = (forecast - committed).days
            deviation = f"{delta_days:+d} дней"
        else:
            deviation = "—"

        if current_block_id:
            current_snapshot = top_snapshots[current_block_id]
            current_title = _compact_text(current_snapshot.title)
            control_point = _gate_text(plan, current_snapshot)
            current_block_cfg = exec_cfg.get("blocks", {}).get(current_block_id, {})
            current_mgmt = _block_mgmt(current_block_cfg if isinstance(current_block_cfg, dict) else {})
            next_goal = current_mgmt.get("next_sync_goal") or "—"
        else:
            current_title = "Все основные этапы завершены"
            control_point = "—"
            next_goal = "—"

        nearest_goal = program.get("nearest_goal") if isinstance(program.get("nearest_goal"), str) else None
        success_by_next_sync = (
            program.get("success_by_next_sync")
            if isinstance(program.get("success_by_next_sync"), str)
            else None
        )

        lines = [
            f"- Обещанная дата: `{_format_date(committed_date)}`",
            f"- Текущий прогноз: `{_format_date(prod_gate_date)}`",
            f"- Отклонение: `{deviation}`",
        ]
        if nearest_goal:
            lines.append(f"- Ближайшая цель: {nearest_goal}")
        if success_by_next_sync:
            lines.append(f"- Что считаем успехом к следующему синку: {success_by_next_sync}")
        lines.extend(
            [
                f"- Текущий этап: `{current_title}`",
                f"- Ближайшая контрольная точка: `{control_point}`",
                f"- Ближайший главный шаг: {next_goal}",
            ]
        )
        return "\n".join(lines)

    if section == "tracks":
        blocks = exec_cfg.get("blocks", {})
        block_ids, snapshots = _view_snapshots(plan, "exec-active-tracks")
        lines = ["### Date-holders", "", _track_table(plan, block_ids, snapshots, blocks)]

        strategic_view = _exec_views(plan).get("exec-strategic-tracks")
        if isinstance(strategic_view, dict):
            strategic_ids, strategic_snapshots = _view_snapshots(plan, "exec-strategic-tracks")
            if strategic_ids:
                lines.extend(
                    [
                        "",
                        "### Стратегические треки приближения миграции",
                        "",
                        _track_table(plan, strategic_ids, strategic_snapshots, blocks),
                    ]
                )
        return "\n".join(lines)

    if section == "signals":
        blocks = exec_cfg.get("blocks", {})
        block_ids, snapshots = _view_snapshots(plan, "exec-active-tracks")
        all_ids = list(block_ids)
        all_snapshots = dict(snapshots)

        strategic_view = _exec_views(plan).get("exec-strategic-tracks")
        if isinstance(strategic_view, dict):
            strategic_ids, strategic_snapshots = _view_snapshots(plan, "exec-strategic-tracks")
            for block_id in strategic_ids:
                if block_id not in all_snapshots:
                    all_ids.append(block_id)
                    all_snapshots[block_id] = strategic_snapshots[block_id]

        rows = _signal_rows(plan, all_ids, all_snapshots, blocks)
        if not rows:
            return "Сейчас в основных треках нет явных yellow/red сигналов или отдельно зафиксированных зависимостей."
        lines = [
            "| Трек | Сигнал | Почему не green / в чём зависимость | К какой вехе это относится |",
            "|---|---|---|---|",
            *rows,
        ]
        return "\n".join(lines)

    raise ExecConfigError(f"Неизвестная секция executive-report: {section}")
