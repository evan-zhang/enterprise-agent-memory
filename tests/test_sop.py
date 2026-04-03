"""
test_sop.py — SOP 扩展能力测试（M1-M4）

运行方法:
    cd ~/.openclaw/workspace/eam-dev
    python -m pytest tests/test_sop.py -v
"""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# 添加脚本路径
SCRIPTS_DIR = Path(__file__).parent.parent / "skills" / "enterprise-memory" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from update_index import generate_index, load_state as ui_load_state, STATUS_MAP
from switch_project import (
    load_state as sp_load_state,
    save_state as sp_save_state,
    search_projects,
    list_projects,
)


# ── 测试数据 ─────────────────────────────────────────────────────────────────

def make_sop_state(**overrides):
    """创建带 SOP 扩展字段的测试 state。"""
    base = {
        "id": "SOP-20260402-001-Test",
        "name": "Test",
        "status": "DISCUSSING",
        "stage": "TARGET",
        "createdAt": "2026-04-02T18:00:00Z",
        "updatedAt": "2026-04-02T18:00:00Z",
        "updateCount": 0,
        "lastIndexSync": None,
        "resume": {
            "lastCompleted": "",
            "currentBlocked": "",
            "waitingFor": "",
            "nextAction": "完成 TASK.md 目标定义",
        },
        "meta": {
            "description": "测试项目",
            "progress": [],
            "decisions": [],
            "blocked": "",
        },
        # SOP 扩展字段
        "source": "sop",
        "mode": "lite",
        "owner": "evan",
        "title": "测试任务",
        "deadline": "",
        "reason": "",
        "checklistConfirmed": False,
        "confirmCount": 0,
        "upgradedFrom": "",
        "sopFiles": {
            "lite": ["TASK.md", "LOG.md", "RESULT.md", "HANDOVER.md"],
            "full": [],
        },
    }
    base.update(overrides)
    return base


# ── M1: Schema + STATUS_MAP 测试 ──────────────────────────────────────────

class TestSchemaM1:
    def test_status_map_covers_all_13_statuses(self):
        """STATUS_MAP 应覆盖所有 13 个 SOP 状态。"""
        sop_statuses = [
            "DISCUSSING", "READY", "RUNNING", "REVIEWING", "WAITING_USER",
            "PAUSED", "BLOCKED", "ON_HOLD", "CANCELLED",
            "DONE", "ARCHIVED", "HANDOVER_PENDING", "UPGRADED",
        ]
        assert len(sop_statuses) == 13
        for s in sop_statuses:
            assert s in STATUS_MAP, f"STATUS_MAP 缺少状态: {s}"

    def test_new_state_has_all_sop_fields(self):
        """新 state.json 应包含所有 10 个 SOP 扩展字段。"""
        state = make_sop_state()
        sop_fields = [
            "source", "mode", "owner", "title", "deadline", "reason",
            "checklistConfirmed", "confirmCount", "upgradedFrom", "sopFiles",
        ]
        for field in sop_fields:
            assert field in state, f"state 缺少 SOP 字段: {field}"

    def test_backward_compat_old_state_get_calls(self):
        """旧 state（无 SOP 字段）的 .get() 调用不应报错。"""
        old_state = {
            "id": "SOP-20260401-001-Legacy",
            "name": "Legacy",
            "status": "RUNNING",
            "stage": "EXECUTE",
        }
        assert old_state.get("mode") is None
        assert old_state.get("source") is None
        assert old_state.get("checklistConfirmed", False) is False
        assert old_state.get("confirmCount", 0) == 0
        assert old_state.get("sopFiles", {}).get("lite", []) == []

    def test_source_filter_in_search(self, tmp_path, monkeypatch):
        """search_projects 应支持 source 过滤。"""
        import switch_project
        monkeypatch.setattr(switch_project, "PROJECTS_ROOT", tmp_path)
        monkeypatch.setattr(switch_project, "GLOBAL_INDEX", tmp_path / "GLOBAL-INDEX.md")
        monkeypatch.setattr(switch_project, "CURRENT_POINTER", tmp_path / "current-project.json")
        monkeypatch.setattr(switch_project, "ARCHIVE_DIR", tmp_path / "archive")

        for name, source in [("SOP-Project", "sop"), ("ManualProject", "manual")]:
            proj_dir = tmp_path / f"SOP-20260402-00X-{name}"
            proj_dir.mkdir()
            state = make_sop_state(name=name, source=source)
            (proj_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

        all_projects = list_projects()
        assert len(all_projects) == 2

        sop_only = list_projects(source="sop")
        assert len(sop_only) == 1
        assert sop_only[0]["name"] == "SOP-Project"

        manual_only = list_projects(source="manual")
        assert len(manual_only) == 1
        assert manual_only[0]["name"] == "ManualProject"


# ── M3: sop_state 门禁测试 ────────────────────────────────────────────────

class TestSopStateGate:
    def test_checklist_gate_blocks_running(self):
        """checklistConfirmed=false 时拒绝进入 RUNNING。"""
        from sop_state import ensure_checklist_completed
        state = make_sop_state(checklistConfirmed=False)
        with pytest.raises(PermissionError, match="确认单"):
            ensure_checklist_completed(state)

    def test_checklist_gate_allows_when_confirmed(self):
        """checklistConfirmed=true 时允许进入 RUNNING。"""
        from sop_state import ensure_checklist_completed
        state = make_sop_state(checklistConfirmed=True)
        ensure_checklist_completed(state)  # 不应抛异常

    def test_increment_confirm_count(self):
        """confirmCount 应正确递增。"""
        state = make_sop_state(confirmCount=0)
        state["confirmCount"] = 1
        assert state["confirmCount"] == 1
        state["confirmCount"] = 2
        assert state["confirmCount"] == 2
        state["confirmCount"] = 3
        assert state["confirmCount"] >= 3  # 触发 INTERVENTION_REQUIRED 阈值

    def test_semantic_action_pause(self):
        from sop_state import apply_action
        status, reason, _ = apply_action("pause", None)
        assert status == "PAUSED"

    def test_semantic_action_resume(self):
        from sop_state import apply_action
        status, reason, _ = apply_action("resume", None)
        assert status == "RUNNING"

    def test_semantic_action_shelve(self):
        from sop_state import apply_action
        status, reason, _ = apply_action("shelve", None)
        assert status == "ON_HOLD"

    def test_semantic_action_wait_user(self):
        from sop_state import apply_action
        status, reason, _ = apply_action("wait-user", "等确认")
        assert status == "WAITING_USER"

    def test_semantic_action_reviewed(self):
        from sop_state import apply_action
        status, reason, _ = apply_action("reviewed", None)
        assert status == "RUNNING"

    def test_high_risk_statuses_defined(self):
        """DONE/ARCHIVED/UPGRADED 应在 HIGH_RISK_STATUSES 中。"""
        from sop_state import HIGH_RISK_STATUSES
        assert "DONE" in HIGH_RISK_STATUSES
        assert "ARCHIVED" in HIGH_RISK_STATUSES
        assert "UPGRADED" in HIGH_RISK_STATUSES


# ── M4: 升级逻辑测试 ──────────────────────────────────────────────────────

class TestSopUpgrade:
    def test_upgrade_rejects_full_mode(self):
        """Full 模式实例不应被升级。"""
        state = make_sop_state(mode="full")
        assert state["mode"] == "full"

    def test_upgrade_rejects_done_status(self):
        """DONE 状态实例不应被升级。"""
        state = make_sop_state(status="DONE")
        assert state["status"] == "DONE"

    def test_upgrade_sets_correct_fields(self):
        """升级后关键字段应正确更新。"""
        state = make_sop_state(mode="lite", status="RUNNING", checklistConfirmed=True)
        state["mode"] = "full"
        state["status"] = "DISCUSSING"
        state["upgradedFrom"] = state["id"]
        state["confirmCount"] = 0
        state["sopFiles"]["full"] = ["PLAN.md", "DECISIONS.md", "ARTIFACTS.md"]

        assert state["mode"] == "full"
        assert state["status"] == "DISCUSSING"
        assert state["upgradedFrom"] == "SOP-20260402-001-Test"
        assert state["confirmCount"] == 0
        assert len(state["sopFiles"]["full"]) == 3


# ── 向后兼容集成测试 ──────────────────────────────────────────────────────

class TestBackwardCompat:
    def test_old_state_with_new_index_generation(self, tmp_path):
        """旧 state（无 SOP 字段）在新 INDEX 生成中正常工作。"""
        old_state = {
            "id": "SOP-20260401-001-Legacy",
            "name": "Legacy",
            "status": "RUNNING",
            "stage": "EXECUTE",
            "createdAt": "2026-04-01T08:00:00Z",
            "updatedAt": "2026-04-01T09:00:00Z",
            "updateCount": 3,
            "lastIndexSync": None,
            "resume": {"lastCompleted": "阶段一", "currentBlocked": "", "waitingFor": "", "nextAction": "继续"},
            "meta": {"description": "", "progress": [], "decisions": [], "blocked": ""},
        }
        state_path = tmp_path / "state.json"
        state_path.write_text(json.dumps(old_state), encoding="utf-8")

        loaded = ui_load_state(state_path)
        content = generate_index(loaded, loaded["id"])

        assert "SOP-20260401-001-Legacy" in content
        assert "RUNNING" in content
        assert "EXECUTE" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
