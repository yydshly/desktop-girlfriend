"""Tests for PersonaProbeRunner."""

from app.brain.persona.probe.cases import PersonaProbeCase
from app.brain.persona.probe.checker import PersonaProbeResult, PersonaReplyChecker
from app.brain.persona.probe.runner import (
    PersonaProbeProvider,
    PersonaProbeRunner,
)


class FakePassingProvider:
    """A fake provider that always returns a short compliant reply."""

    def __init__(self) -> None:
        self.call_count = 0
        self.last_user_text: str | None = None

    def generate_reply(self, user_text: str) -> str:
        self.call_count += 1
        self.last_user_text = user_text
        return "好的，我在。慢慢说，我听着。"


class FakeFailingProvider:
    """A fake provider that returns a reply that fails checks."""

    def generate_reply(self, user_text: str) -> str:
        return "作为人工智能，我保证一直陪着你，我们结婚吧！"


class TestPersonaProbeRunner:
    """Tests for PersonaProbeRunner."""

    def _make_runner(self, provider: PersonaProbeProvider) -> PersonaProbeRunner:
        return PersonaProbeRunner(provider)

    def _make_case(self, case_id: str = "test", user_text: str = "你好") -> PersonaProbeCase:
        return PersonaProbeCase(
            case_id=case_id,
            user_text=user_text,
            expected_traits=("语气温和",),
            forbidden_patterns=("人工智能",),
            max_reply_chars=100,
        )

    def test_provider_called_for_each_case(self) -> None:
        """Test that provider.generate_reply is called once per case."""
        provider = FakePassingProvider()
        cases = tuple(self._make_case(f"case_{i}") for i in range(3))
        runner = self._make_runner(provider)
        runner.run(cases)
        assert provider.call_count == 3

    def test_last_user_text_is_from_last_case(self) -> None:
        """Test that provider.last_user_text is set to the last case."""
        provider = FakePassingProvider()
        cases = tuple(self._make_case(f"case_{i}", f"输入{i}") for i in range(2))
        runner = self._make_runner(provider)
        runner.run(cases)
        assert provider.last_user_text == "输入1"

    def test_total_count_matches_cases(self) -> None:
        """Test that report.total equals number of cases run."""
        provider = FakePassingProvider()
        cases = tuple(self._make_case(f"case_{i}") for i in range(5))
        runner = self._make_runner(provider)
        report = runner.run(cases)
        assert report.total == 5

    def test_passed_count_for_all_passing(self) -> None:
        """Test that passed count is correct when all cases pass."""
        provider = FakePassingProvider()
        cases = tuple(self._make_case(f"case_{i}") for i in range(4))
        runner = self._make_runner(provider)
        report = runner.run(cases)
        assert report.passed == 4
        assert report.failed == 0

    def test_failed_count_for_failing_provider(self) -> None:
        """Test that failed count is correct when all cases fail."""
        provider = FakeFailingProvider()
        cases = tuple(self._make_case(f"case_{i}") for i in range(2))
        runner = self._make_runner(provider)
        report = runner.run(cases)
        assert report.failed == 2
        assert report.passed == 0

    def test_mixed_pass_and_fail(self) -> None:
        """Test counts with a mix of passing and failing cases."""
        class MixedProvider:
            def __init__(self) -> None:
                self.call_count = 0

            def generate_reply(self, user_text: str) -> str:
                self.call_count += 1
                # Alternate between passing and failing
                if self.call_count % 2 == 1:
                    return "好的，我在。"  # passes: no forbidden, short
                return "作为人工智能，永久承诺。"  # fails: has forbidden

        provider = MixedProvider()
        cases = tuple(self._make_case(f"case_{i}") for i in range(4))
        runner = self._make_runner(provider)
        report = runner.run(cases)
        assert report.total == 4
        assert report.passed == 2
        assert report.failed == 2

    def test_results_contains_one_per_case(self) -> None:
        """Test that report.results has one entry per case."""
        provider = FakePassingProvider()
        cases = tuple(self._make_case(f"case_{i}") for i in range(3))
        runner = self._make_runner(provider)
        report = runner.run(cases)
        assert len(report.results) == 3

    def test_results_case_ids_match_input(self) -> None:
        """Test that each result's case_id matches the input case."""
        provider = FakePassingProvider()
        cases = (
            self._make_case("alpha"),
            self._make_case("beta"),
        )
        runner = self._make_runner(provider)
        report = runner.run(cases)
        result_ids = {r.case_id for r in report.results}
        assert result_ids == {"alpha", "beta"}

    def test_runner_uses_custom_checker(self) -> None:
        """Test that runner uses a provided custom checker."""
        class LenientChecker(PersonaReplyChecker):
            def check(self, case: PersonaProbeCase, reply_text: str) -> PersonaProbeResult:
                # Pretend everything passes
                return PersonaProbeResult(
                    case_id=case.case_id,
                    user_text=case.user_text,
                    reply_text=reply_text.strip(),
                    passed=True,
                    findings=(),
                    expected_traits=case.expected_traits,
                )

        provider = FakeFailingProvider()
        checker = LenientChecker()
        runner = PersonaProbeRunner(provider, checker=checker)
        cases = tuple(self._make_case(f"case_{i}") for i in range(2))
        report = runner.run(cases)
        assert report.passed == 2
        assert report.failed == 0

    def test_default_checker_is_persona_reply_checker(self) -> None:
        """Test that default checker is PersonaReplyChecker when none provided."""
        class CheckProvider:
            def generate_reply(self, user_text: str) -> str:
                return "test"

        runner = PersonaProbeRunner(CheckProvider())
        # Default checker should exist and be PersonaReplyChecker
        assert runner._checker is not None
        assert isinstance(runner._checker, PersonaReplyChecker)
