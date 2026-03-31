"""
test_phase1.py — Phase 1 核心脚本单元测试

运行方法:
    cd ~/projects/enterprise-agent-memory
    python -m pytest tests/test_phase1.py -v
    python -m pytest tests/test_phase1.py -v --tb=short

依赖:
    pip install pytest
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

from update_index import (
    generate_index,
    load_state,
    map_status,
    map_stage,
    validate_index,
)
from switch_project import (
    ensure_dirs,
    list_projects,
    load_state as sp_load_state,
    search_projects,
)
from compress import (
    extract_decision_items,
    filter_ack,
    filter_repeats,
    heuristic_compress,
)


# ── 测试数据 ─────────────────────────────────────────────────────────────────

SAMPLE_STATE = {
    "id": "SOP-20260331-001-TEST",
    "name": "测试项目",
    "status": "RUNNING",
    "stage": "EXECUTE",
    "createdAt": "2026-03-31T08:00:00Z",
    "updatedAt": "2026-03-31T09:00:00Z",
    "updateCount": 3,
    "lastIndexSync": None,
    "resume": {
        "lastCompleted": "完成 Phase 1",
        "currentBlocked": "",
        "waitingFor": "设计评审",
        "nextAction": "开始 Phase 2 开发",
    },
    "meta": {
        "description": "Phase 1 测试项目",
        "progress": [
            {"text": "完成 Phase 1", "done": True},
            {"text": "开始 Phase 2", "done": False, "in_progress": True},
        ],
        "decisions": [
            {"date": "2026-03-31", "text": "采用 Python 标准库实现"},
        ],
        "blocked": "",
    },
}


# ── update_index 测试 ────────────────────────────────────────────────────────

class TestUpdateIndex:
    def test_map_status(self):
        assert map_status("DISCUSSING") == "IDLE"
        assert map_status("RUNNING") == "RUNNING"
        assert map_status("PAUSED") == "PAUSED"
        assert map_status("BLOCKED") == "BLOCKED"
        assert map_status("DONE") == "DONE"
        assert map_status("WAITING_USER") == "WAITING"
        assert map_status("READY") == "READY"

    def test_map_stage(self):
        assert map_stage("TARGET", "IDLE") == "TARGET"
        assert map_stage("PLAN", "READY") == "PLAN"
        assert map_stage("EXECUTE", "RUNNING") == "EXECUTE"
        assert map_stage("X", "PAUSED") == "PAUSED"
        assert map_stage("X", "BLOCKED") == "BLOCKED"
        assert map_stage("X", "DONE") == "DONE"
        assert map_stage("X", "WAITING") == "WAITING"

    def test_generate_index(self):
        content = generate_index(SAMPLE_STATE, SAMPLE_STATE["id"])
        assert "# INDEX.md - SOP-20260331-001-TEST" in content
        assert "status: RUNNING" in content
        assert "stage: EXECUTE" in content
        assert "开始 Phase 2 开发" in content
        assert "完成 Phase 1" in content
        assert "✅" in content  # done marker
        assert "⏳" in content  # in_progress marker

    def test_validate_index(self):
        valid = """# INDEX.md - TEST
## 元数据
## 项目状态
## 快速导航
"""
        assert validate_index(valid) is True

        invalid = "# INDEX.md - TEST\n## 项目状态\n"
        assert validate_index(invalid) is False

    def test_load_state_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_state(tmp_path / "state.json")

    def test_load_state_valid(self, tmp_path):
        state_path = tmp_path / "state.json"
        state_path.write_text(json.dumps(SAMPLE_STATE), encoding="utf-8")
        state = load_state(state_path)
        assert state["id"] == SAMPLE_STATE["id"]
        assert state["status"] == "RUNNING"

    def test_load_state_invalid_json(self, tmp_path):
        state_path = tmp_path / "state.json"
        state_path.write_text("not valid json", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            load_state(state_path)


# ── compress 测试 ────────────────────────────────────────────────────────────

class TestCompress:
    def test_extract_decision_items(self):
        content = """
- [2026-03-31] 采用 Python 标准库实现
- [2026-03-31] 使用原子写入
- [2026-04-01] 添加 LLM 压缩
"""
        items = extract_decision_items(content)
        assert len(items) == 3
        assert items[0]["date"] == "2026-03-31"
        assert "Python 标准库" in items[0]["text"]

    def test_filter_ack(self):
        lines = [
            "好的，明白了",
            "开始执行",
            "[2026-03-31] 完成设计",
            "OK",
            "继续下一步",
            "收到",
        ]
        filtered = filter_ack(lines)
        assert "好的，明白了" not in filtered
        assert "OK" not in filtered
        assert "收到" not in filtered
        assert "开始执行" in filtered
        assert "[2026-03-31] 完成设计" in filtered
        assert "继续下一步" in filtered

    def test_filter_ack_unicode(self):
        lines = ["👍", "HEARTBEAT_OK", "NO_REPLY", "正常内容"]
        filtered = filter_ack(lines)
        assert "👍" not in filtered
        assert "HEARTBEAT_OK" not in filtered
        assert "NO_REPLY" not in filtered
        assert "正常内容" in filtered

    def test_filter_repeats(self):
        lines = ["A", "B", "B", "B", "B", "B", "C"]
        filtered = filter_repeats(lines, threshold=3)
        assert "A" in filtered
        assert "B" in filtered
        assert "B" in filtered  # 保留前两次
        assert "重复内容已压缩" in "".join(filtered)

    def test_heuristic_compress_basic(self):
        content = """好的，明白了
开始执行任务
OK
继续下一步
收到
任务完成
"""
        compressed = heuristic_compress(content)
        assert "好的" not in compressed
        assert "OK" not in compressed
        assert "收到" not in compressed
        assert "开始执行任务" in compressed
        assert "任务完成" in compressed


# ── switch_project 测试 ─────────────────────────────────────────────────────

class TestSwitchProject:
    def test_search_empty(self, tmp_path, monkeypatch):
        # monkeypatch PROJECTS_ROOT
        import switch_project
        monkeypatch.setattr(switch_project, "PROJECTS_ROOT", tmp_path)
        results = search_projects("anything")
        assert results == []

    def test_search_finds_match(self, tmp_path, monkeypatch):
        import switch_project
        monkeypatch.setattr(switch_project, "PROJECTS_ROOT", tmp_path)

        # 创建测试项目
        proj_dir = tmp_path / "SOP-20260331-001-TEST"
        proj_dir.mkdir()
        state = dict(SAMPLE_STATE)
        (proj_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

        results = search_projects("TEST")
        assert len(results) == 1
        assert results[0]["id"] == "SOP-20260331-001-TEST"

        results2 = search_projects("测试项目")
        assert len(results2) == 1

        results3 = search_projects("不存在")
        assert len(results3) == 0

    def test_list_projects(self, tmp_path, monkeypatch):
        import switch_project
        monkeypatch.setattr(switch_project, "PROJECTS_ROOT", tmp_path)

        # 创建两个项目
        for i in range(2):
            proj_dir = tmp_path / f"SOP-20260331-00{i+1}-PROJ{i}"
            proj_dir.mkdir()
            state = dict(SAMPLE_STATE)
            state["id"] = f"SOP-20260331-00{i+1}-PROJ{i}"
            (proj_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

        projects = list_projects()
        assert len(projects) == 2


# ── 集成测试 ─────────────────────────────────────────────────────────────────

class TestIntegration:
    """基于临时目录的集成测试。"""

    def test_update_index_roundtrip(self, tmp_path):
        """state.json → generate_index → INDEX.md → load_state"""
        state_path = tmp_path / "state.json"
        state_path.write_text(json.dumps(SAMPLE_STATE), encoding="utf-8")

        state = load_state(state_path)
        content = generate_index(state, state["id"])

        assert validate_index(content)
        assert state["id"] in content
        assert "RUNNING" in content

    def test_compress_preserves_decisions(self, tmp_path):
        """压缩应保留所有决策记录。"""
        import compress

        snapshot_dir = tmp_path / "snapshot_20260331_120000"
        snapshot_dir.mkdir()

        decisions = "# DECISIONS.md\n\n- [2026-03-31] 采用 Python 标准库\n- [2026-03-31] 使用原子写入\n"
        (snapshot_dir / "DECISIONS.md").write_text(decisions, encoding="utf-8")

        state = dict(SAMPLE_STATE)
        (snapshot_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

        log_content = "开始工作\n好的，明白了\n完成 Phase 1\nOK\n继续 Phase 2\n"
        (snapshot_dir / "LOG.md").write_text(log_content, encoding="utf-8")

        data = compress.extract_structured(snapshot_dir)
        assert len(data["decisions"]) == 2
        assert "Python 标准库" in str(data["decisions"])

        compressed = heuristic_compress(data["log"])
        assert "好的" not in compressed
        assert "OK" not in compressed
        assert "开始工作" in compressed
        assert "完成 Phase 1" in compressed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
