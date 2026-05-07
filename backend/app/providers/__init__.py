"""Provider adapters package. Importing registers all built-in providers."""

# Side-effect imports register subclasses with the factory.
from app.providers import anthropic, google, openai  # noqa: F401
from app.providers.base import (  # noqa: F401
    Provider,
    list_providers,
    make_provider,
    register_provider,
)
