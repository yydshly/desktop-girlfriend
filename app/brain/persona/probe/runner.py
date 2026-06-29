"""Runner that drives persona probe cases through a provider."""

from dataclasses import dataclass, field
from typing import Protocol

from app.brain.persona.probe.cases import PersonaProbeCase
from app.brain.persona.probe.checker import (
    PersonaProbeResult,
    PersonaReplyChecker,
)


class PersonaProbeProvider(Protocol):
    """Protocol for a provider that can generate replies for probe cases.

    Implement this protocol to adapt any chat provider to the probe runner.
    """

    def generate_reply(self, user_text: str) -> str:
        """Generate a reply for the given user text.

        Args:
            user_text: The user input text.

        Returns:
            The generated reply text.
        """
        ...


@dataclass(frozen=True)
class PersonaProbeReport:
    """Summary report from a persona probe run.

    Attributes:
        total: Total number of cases run.
        passed: Number of cases that passed all checks.
        failed: Number of cases that had at least one finding.
        results: Tuple of per-case results.
    """

    total: int
    passed: int
    failed: int
    results: tuple[PersonaProbeResult, ...] = field(default_factory=tuple)


class PersonaProbeRunner:
    """Runs persona probe cases through a provider and checks replies."""

    def __init__(
        self,
        provider: PersonaProbeProvider,
        checker: PersonaReplyChecker | None = None,
    ) -> None:
        """Initialize the runner.

        Args:
            provider: A provider that can generate replies.
            checker: Optional reply checker. Defaults to PersonaReplyChecker().
        """
        self._provider = provider
        self._checker = checker if checker is not None else PersonaReplyChecker()

    def run(
        self,
        cases: tuple[PersonaProbeCase, ...],
    ) -> PersonaProbeReport:
        """Run all probe cases through the provider and check replies.

        Args:
            cases: Tuple of probe cases to run.

        Returns:
            A PersonaProbeReport with per-case results and summary statistics.
        """
        results: list[PersonaProbeResult] = []
        for case in cases:
            reply = self._provider.generate_reply(case.user_text)
            result = self._checker.check(case, reply)
            results.append(result)

        results_tuple = tuple(results)
        passed = sum(1 for r in results_tuple if r.passed)
        failed = len(results_tuple) - passed

        return PersonaProbeReport(
            total=len(results_tuple),
            passed=passed,
            failed=failed,
            results=results_tuple,
        )
