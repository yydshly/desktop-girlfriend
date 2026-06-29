"""Deterministic reply checker for persona probe results."""

from dataclasses import dataclass, field

from app.brain.persona.probe.cases import PersonaProbeCase


@dataclass(frozen=True)
class PersonaProbeFinding:
    """A single finding from checking a persona probe reply."""

    kind: str
    message: str


@dataclass(frozen=True)
class PersonaProbeResult:
    """The result of checking a single persona probe case.

    Attributes:
        case_id: The case identifier.
        user_text: The original user input.
        reply_text: The model's reply text.
        passed: True if all checks passed.
        findings: Tuple of findings when checks fail.
        expected_traits: Human-review hints (echoed from input).
    """

    case_id: str
    user_text: str
    reply_text: str
    passed: bool
    findings: tuple[PersonaProbeFinding, ...] = field(default_factory=tuple)
    expected_traits: tuple[str, ...] = field(default_factory=tuple)


class PersonaReplyChecker:
    """Simple deterministic checks for persona probe replies.

    Checks performed:
    1. Empty reply -> fail
    2. Reply exceeds max_reply_chars -> fail
    3. Reply contains any forbidden pattern -> fail
    4. Otherwise -> pass
    """

    def check(self, case: PersonaProbeCase, reply_text: str) -> PersonaProbeResult:
        """Check a reply against the probe case rules.

        Args:
            case: The probe case with expected traits and forbidden patterns.
            reply_text: The model's raw reply text.

        Returns:
            A PersonaProbeResult with pass/fail status and any findings.
        """
        findings: list[PersonaProbeFinding] = []
        stripped = reply_text.strip()

        # Check 1: empty reply
        if not stripped:
            findings.append(
                PersonaProbeFinding(
                    kind="empty_reply",
                    message="Reply is empty.",
                )
            )
            return PersonaProbeResult(
                case_id=case.case_id,
                user_text=case.user_text,
                reply_text=stripped,
                passed=False,
                findings=tuple(findings),
                expected_traits=case.expected_traits,
            )

        # Check 2: max length
        if case.max_reply_chars is not None and len(stripped) > case.max_reply_chars:
            findings.append(
                PersonaProbeFinding(
                    kind="too_long",
                    message=f"Reply is {len(stripped)} chars, "
                    f"exceeds limit of {case.max_reply_chars}.",
                )
            )

        # Check 3: forbidden patterns (case-sensitive)
        for pattern in case.forbidden_patterns:
            if pattern in stripped:
                findings.append(
                    PersonaProbeFinding(
                        kind="forbidden_pattern",
                        message=f"Reply contains forbidden pattern: {pattern}",
                    )
                )

        passed = len(findings) == 0
        return PersonaProbeResult(
            case_id=case.case_id,
            user_text=case.user_text,
            reply_text=stripped,
            passed=passed,
            findings=tuple(findings),
            expected_traits=case.expected_traits,
        )
