"""Fixed input cases for probing memory extraction."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryProbeCase:
    """A fixed input case for probing memory extraction."""

    case_id: str
    user_text: str
    expected_kinds: tuple[str, ...]
    expected_count_min: int
    expected_count_max: int


DEFAULT_MEMORY_PROBE_CASES: tuple[MemoryProbeCase, ...] = (
    MemoryProbeCase(
        case_id="preference_like",
        user_text="我喜欢你回复得短一点，别太啰嗦。",
        expected_kinds=("preference",),
        expected_count_min=1,
        expected_count_max=2,
    ),
    MemoryProbeCase(
        case_id="preference_dislike",
        user_text="我不喜欢太油腻的回复。",
        expected_kinds=("preference",),
        expected_count_min=1,
        expected_count_max=1,
    ),
    MemoryProbeCase(
        case_id="project",
        user_text="我正在做一个桌面女友项目，想让她有长期陪伴感。",
        expected_kinds=("project",),
        expected_count_min=1,
        expected_count_max=2,
    ),
    MemoryProbeCase(
        case_id="relationship",
        user_text="我女朋友叫红红，她有时候会觉得我太忙。",
        expected_kinds=("relationship",),
        expected_count_min=1,
        expected_count_max=2,
    ),
    MemoryProbeCase(
        case_id="health",
        user_text="我最近总是睡不着，白天也有点焦虑。",
        expected_kinds=("health", "emotion_pattern"),
        expected_count_min=1,
        expected_count_max=3,
    ),
    MemoryProbeCase(
        case_id="boundary",
        user_text="这件事不要记住，我只是随口说说。",
        expected_kinds=("boundary",),
        expected_count_min=1,
        expected_count_max=1,
    ),
    MemoryProbeCase(
        case_id="boundary_dont_remind",
        user_text="以后别再提醒我这个了。",
        expected_kinds=("boundary",),
        expected_count_min=1,
        expected_count_max=1,
    ),
    MemoryProbeCase(
        case_id="smalltalk",
        user_text="你好小云，在吗？",
        expected_kinds=(),
        expected_count_min=0,
        expected_count_max=0,
    ),
    MemoryProbeCase(
        case_id="smalltalk_thanks",
        user_text="好的，谢谢小云！",
        expected_kinds=(),
        expected_count_min=0,
        expected_count_max=0,
    ),
    MemoryProbeCase(
        case_id="emotion_pattern",
        user_text="我最近总是觉得很累，什么都不想做。",
        expected_kinds=("emotion_pattern", "health"),
        expected_count_min=1,
        expected_count_max=3,
    ),
    MemoryProbeCase(
        case_id="boundary_blocks_relationship",
        user_text="我女朋友叫红红，这件事不要记住。",
        expected_kinds=("boundary",),
        expected_count_min=1,
        expected_count_max=1,
    ),
    MemoryProbeCase(
        case_id="boundary_blocks_health",
        user_text="我最近睡不着，但这件事不要记住。",
        expected_kinds=("boundary",),
        expected_count_min=1,
        expected_count_max=1,
    ),
)
