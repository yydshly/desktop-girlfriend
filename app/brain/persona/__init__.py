"""Persona module for structured companion identity."""

from app.brain.persona.defaults import DEFAULT_XIAOYUN_PERSONA
from app.brain.persona.profile import PersonaProfile
from app.brain.persona.prompt_builder import PersonaPromptBuilder

__all__ = [
    "DEFAULT_XIAOYUN_PERSONA",
    "PersonaProfile",
    "PersonaPromptBuilder",
]
