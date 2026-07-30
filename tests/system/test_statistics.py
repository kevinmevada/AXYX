from motion_engine.rendering.runtime.runtime_statistics import RuntimeStatistics
from motion_engine.rendering.runtime.types import PipelineFrame


def test_statistics_report():
    s = RuntimeStatistics()
    for i in range(5):
        s.add(
            PipelineFrame(
                index=i,
                time=i / 30.0,
                pose_name="p",
                vertex_count=10,
                bone_count=2,
                finite=True,
                stages_ns={"frame": 1000 + i, "retarget": 500, "skinning": 500},
            )
        )
    r = s.report(phase="playing")
    assert r.frames == 5
    assert r.fps > 0
