r"""Probe script to inspect the generated persona system prompt.

Run:
    .venv\Scripts\python.exe scripts\probe_persona_prompt.py
"""

from app.brain.persona import DEFAULT_XIAOYUN_PERSONA, PersonaPromptBuilder
from app.core.config import get_config


def main() -> None:
    config = get_config()

    print(f"persona_name: {config.persona_name}")
    print(f"persona_user_address: {config.persona_user_address}")

    # Build from default persona with config overrides
    from dataclasses import replace

    profile = replace(
        DEFAULT_XIAOYUN_PERSONA,
        name=config.persona_name,
        user_address=config.persona_user_address,
    )
    builder = PersonaPromptBuilder(profile)
    prompt = builder.build_system_prompt()

    print(f"system_prompt_chars: {len(prompt)}")
    print()
    print("system_prompt_preview:")
    print(prompt[:500])
    print("...")


if __name__ == "__main__":
    main()
