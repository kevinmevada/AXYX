from motion_engine.rendering.runtime import RuntimeFactory


def test_session_fields():
    rt = RuntimeFactory().debug()
    rt.startup()
    rt.select_subject("S1")
    rt.select_trial("T1")
    rt.select_avatar("fixture")
    d = rt.session.as_dict()
    assert d["subject_id"] == "S1"
    assert d["trial_id"] == "T1"
    rt.shutdown()
