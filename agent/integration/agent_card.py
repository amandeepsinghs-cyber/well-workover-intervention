"""Agent card capabilities declaration for Gemini Enterprise and Agent Registry."""

from a2a.types import AgentCapabilities, AgentExtension

ADK_AGENT_EXECUTOR_EXTENSION_URI: str = (
    "https://google.github.io/adk-docs/a2a/a2a-extension/"
)
A2UI_V09_EXTENSION_URI: str = "https://a2ui.org/a2a-extension/a2ui/v0.9"
DEFAULT_GE_CATALOG_ID: str = (
    "https://www.gstatic.com/vertexaisearch/a2ui/v0_9/gemini_enterprise_composite_catalog.json"
)


def build_agent_capabilities() -> AgentCapabilities:
    """Declare streaming and A2UI v0.9 composite catalog support on the A2A Agent Card."""
    from google.protobuf.struct_pb2 import Struct

    catalog_params = Struct()
    catalog_params.update({"supportedCatalogIds": [DEFAULT_GE_CATALOG_ID]})

    return AgentCapabilities(
        streaming=True,
        extensions=[
            AgentExtension(
                uri=ADK_AGENT_EXECUTOR_EXTENSION_URI,
                description="Ability to use the modern ADK agent executor implementation",
            ),
            AgentExtension(
                uri=A2UI_V09_EXTENSION_URI,
                description="Ability to render rich A2UI v0.9 interactive components (VegaChart, Card)",
                params=catalog_params,
            ),
        ],
    )
