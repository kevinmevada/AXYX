"""Launch the AXYX Studio viewer on S2 / WU01."""

from __future__ import annotations

from motion_engine import MotionDatabase, SkeletonBuilder, SkeletonViewer


def main() -> None:
    skeleton = SkeletonBuilder().build(
        MotionDatabase().load().get_subject("S2").get_session("WU01")
    )
    SkeletonViewer().show(skeleton)


if __name__ == "__main__":
    main()
