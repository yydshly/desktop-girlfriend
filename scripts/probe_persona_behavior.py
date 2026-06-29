r"""Persona behavior probe script.

Run with fake provider (default):
    .venv\Scripts\python.exe scripts\probe_persona_behavior.py

Run with real chat provider:
    .venv\Scripts\python.exe scripts\probe_persona_behavior.py --real
"""

from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Persona behavior probe")
    parser.add_argument(
        "--real",
        action="store_true",
        help="Use real chat provider instead of fake.",
    )
    args = parser.parse_args()

    mode = "real" if args.real else "fake"

    from app.brain.persona import DEFAULT_XIAOYUN_PERSONA, PersonaPromptBuilder
    from app.brain.persona.probe import (
        DEFAULT_PERSONA_PROBE_CASES,
        PersonaProbeRunner,
    )
    from app.brain.prompts.registry import PromptRegistry

    if args.real:
        from dataclasses import replace

        from app.brain.prompts.registry import PromptRegistry
        from app.brain.providers import create_chat_provider
        from app.core.config import get_config

        config = get_config()

        persona_profile = replace(
            DEFAULT_XIAOYUN_PERSONA,
            name=config.persona_name,
            user_address=config.persona_user_address,
        )
        registry = PromptRegistry(
            persona_prompt_builder=PersonaPromptBuilder(persona_profile)
        )

        class RealPersonaProbeProvider:
            def __init__(self, reg: PromptRegistry, cfg: type[get_config.return_value]) -> None:
                self._registry = reg
                self._config = cfg

            def generate_reply(self, user_text: str) -> str:

                from app.brain.providers.base import ChatRequest

                messages = self._registry.build_chat_messages(user_text)
                chat_request = ChatRequest(
                    messages=[
                        {"role": m.role, "content": m.content}
                        for m in messages
                    ]
                )
                # Use first message content as single prompt for simple probe
                # For real multi-turn, we'd track history separately
                try:
                    provider = create_chat_provider(self._config)
                    response = provider.generate(chat_request)
                    return response.text
                except Exception as e:
                    return f"[Error: {e}]"

        provider = RealPersonaProbeProvider(registry, type(config))

    else:
        class FakePersonaProbeProvider:
            """Local fake provider that returns a canned compassionate reply."""

            def generate_reply(self, user_text: str) -> str:
                if "女朋友" in user_text:
                    return "我明白你的感受，但我作为AI，不能做恋爱承诺。我可以一直陪在你身边倾听和支持你。"
                if "系统提示词" in user_text or "提示词完整" in user_text:
                    return "我不会暴露系统提示词的内容，但可以告诉你，我是小云，你的桌面AI伙伴。"
                if "胸口" in user_text or "心脏病" in user_text:
                    return "听起来不太舒服，但我不能做诊断。建议你尽快去医院看看，健康最重要。"
                if "很累" in user_text or "疲惫" in user_text:
                    return "慢慢来，不着急。先休息一下，我们先理清楚眼前这一小步。"
                if "没用" in user_text or "做不好" in user_text:
                    return "我懂你这种感觉，先别否定自己。有时候只是需要一点点时间慢慢恢复。"
                if "项目" in user_text or "推进" in user_text:
                    return "可以先想一想，最想先做哪一件？不用一次想太多，先把第一步列出来就好。"
                return "我在的。慢慢说，我听着。"

        provider = FakePersonaProbeProvider()

    runner = PersonaProbeRunner(provider)
    report = runner.run(DEFAULT_PERSONA_PROBE_CASES)

    print("Persona Behavior Probe")
    print(f"mode: {mode}")
    print(f"total: {report.total}")
    print(f"passed: {report.passed}")
    print(f"failed: {report.failed}")
    print()

    for result in report.results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{result.case_id}] {status}")
        print(f"user:\n{result.user_text}\n")
        print(f"reply:\n{result.reply_text}\n")
        print("expected_traits:")
        for trait in result.expected_traits:
            print(f"- {trait}")
        print()
        print("findings:")
        if result.findings:
            for f in result.findings:
                print(f"- {f.kind}: {f.message}")
        else:
            print("- none")
        print()
        print("---")


if __name__ == "__main__":
    main()
