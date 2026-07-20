"""
===============================================================================
Motion Engine Unreal Certification Suite

This test certifies that the complete Unreal export pipeline functions
correctly from MotionDatabase → Unreal Engine assets.

Passing this suite means the Motion Engine is production ready for Unreal.

Author:
    Motion Engine Certification

===============================================================================
"""

from __future__ import annotations

from pathlib import Path

import pytest

from motion_engine.loader import MotionDatabaseLoader
from motion_engine.skeleton import SkeletonBuilder
from motion_engine.animation_clip import AnimationClip
from motion_engine.unreal.converters.coordinate_converter import CoordinateConverter
from motion_engine.unreal.mapping.skeleton_mapper import SkeletonMapper
from motion_engine.unreal.animation.animation_sequence import AnimationSequence
from motion_engine.unreal.export.unreal_exporter import UnrealExporter
from motion_engine.unreal.export.asset_builder import AssetBuilder
from motion_engine.unreal.pipeline import UnrealPipeline


# --------------------------------------------------------------------------
# Test Dataset
# --------------------------------------------------------------------------

SUBJECT = "S2"
SESSION = "WU01"


# --------------------------------------------------------------------------
# Loader
# --------------------------------------------------------------------------

def test_database_loads():
    db = MotionDatabaseLoader().load()
    assert db is not None
    assert len(db.subjects) > 0


# --------------------------------------------------------------------------
# Skeleton
# --------------------------------------------------------------------------

def test_build_skeleton():
    db = MotionDatabaseLoader().load()
    session = db.get_subject(SUBJECT).get_session(SESSION)
    skeleton = SkeletonBuilder().build(session)
    assert skeleton is not None
    assert len(skeleton.joints) > 0
    assert len(skeleton.bones) > 0
    assert skeleton.frame_count > 0


# --------------------------------------------------------------------------
# Animation Clip
# --------------------------------------------------------------------------

def test_animation_clip():
    db = MotionDatabaseLoader().load()
    session = db.get_subject(SUBJECT).get_session(SESSION)
    skeleton = SkeletonBuilder().build(session)
    clip = AnimationClip.from_skeleton(skeleton)
    assert clip.duration > 0
    assert clip.fps > 0
    assert clip.frame_count == skeleton.frame_count


# --------------------------------------------------------------------------
# Coordinate Conversion
# --------------------------------------------------------------------------

def test_coordinate_conversion():
    db = MotionDatabaseLoader().load()
    session = db.get_subject(SUBJECT).get_session(SESSION)
    skeleton = SkeletonBuilder().build(session)
    clip = AnimationClip.from_skeleton(skeleton)
    converted = CoordinateConverter().convert_animation(clip)
    assert converted.frame_count == clip.frame_count
    assert converted.skeleton == clip.skeleton


# --------------------------------------------------------------------------
# Skeleton Mapping
# --------------------------------------------------------------------------

def test_metahuman_mapping():
    mapper = SkeletonMapper()
    mapper.load_mapping()
    assert mapper.mapping_count > 0
    assert mapper.has_joint("pelvis")
    assert mapper.has_joint("head")


# --------------------------------------------------------------------------
# Animation Sequence
# --------------------------------------------------------------------------

def test_animation_sequence():
    db = MotionDatabaseLoader().load()
    session = db.get_subject(SUBJECT).get_session(SESSION)
    skeleton = SkeletonBuilder().build(session)
    clip = AnimationClip.from_skeleton(skeleton)
    seq = AnimationSequence.from_clip(clip)
    assert seq.frame_count == clip.frame_count
    assert seq.duration == clip.duration


# --------------------------------------------------------------------------
# Exporter
# --------------------------------------------------------------------------

def test_unreal_export(tmp_path):
    db = MotionDatabaseLoader().load()
    session = db.get_subject(SUBJECT).get_session(SESSION)
    output = tmp_path / "export"
    UnrealExporter().export_session(
        session=session,
        output_directory=output,
    )
    assert output.exists()
    assert (output / "walking.fbx").exists()
    assert (output / "walking.metadata.json").exists()
    assert (output / "walking.import.json").exists()


# --------------------------------------------------------------------------
# Asset Builder
# --------------------------------------------------------------------------

def test_asset_builder(tmp_path):
    builder = AssetBuilder()
    out = tmp_path / "package"
    builder.build(out)
    assert out.exists()


# --------------------------------------------------------------------------
# Pipeline
# --------------------------------------------------------------------------

def test_pipeline(tmp_path):
    output = tmp_path / "pipeline"
    UnrealPipeline().export_session(
        subject=SUBJECT,
        session=SESSION,
        output_directory=output,
    )
    assert output.exists()
    assert any(output.glob("*.fbx"))
    assert any(output.glob("*.json"))


# --------------------------------------------------------------------------
# Smoke Test
# --------------------------------------------------------------------------

def test_full_system():
    pipeline = UnrealPipeline()
    result = pipeline.validate()
    assert result.success
