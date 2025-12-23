from typing import Any

from task.tools.deployment.base_agent_tool import BaseAgentTool


class ContentManagementAgentTool(BaseAgentTool):

    # Provide implementations of deployment_name (in core config), name, description and parameters.
    # Don't forget to mark them as @property
    # Parameters:
    #   - prompt: string. Required.
    #   - propagate_history: boolean

    @property
    def deployment_name(self) -> str:
        return "content-management-agent"

    @property
    def name(self) -> str:
        return "content_management_agent"
    @property
    def description(self) -> str:
        return "This agent can read files in different formats and query their contents with semantic search."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Query about the content of the files."
                },
                "propagate_history": {
                    "type": "boolean",
                    "default": False,
                    "description": ("If true, the conversation history is shared with this agent.")
                },
            },
            "required": [
                "prompt"
            ]
        }
