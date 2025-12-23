import os

import uvicorn
from aidial_sdk import DIALApp
from aidial_sdk.chat_completion import ChatCompletion, Request, Response

from task.agents.web_search.web_search_agent import WebSearchAgent
from task.tools.base_tool import BaseTool
from task.tools.deployment.calculations_agent_tool import CalculationsAgentTool
from task.tools.deployment.content_management_agent_tool import ContentManagementAgentTool
from task.tools.mcp.mcp_client import MCPClient
from task.tools.mcp.mcp_tool import MCPTool
from task.utils.constants import DIAL_ENDPOINT, DEPLOYMENT_NAME

_DDG_MCP_URL = os.getenv('DDG_MCP_URL', "http://localhost:8051/mcp")

# 1. Create WebSearchApplication class and extend ChatCompletion
# 2. As a tools for WebSearchAgent you need to provide:
#   - MCP tools by _DDG_MCP_URL
#   - CalculationsAgentTool (MAS Mesh)
#   - ContentManagementAgentTool (MAS Mesh)
# 3. Override the chat_completion method of ChatCompletion, create Choice and call WebSearchAgent
# ---
# 4. Create DIALApp with deployment_name `web-search-agent` (the same as in the core config) and impl is instance
#    of the WebSearchApplication
# 5. Add starter with DIALApp, port is 5003 (see core config)

class WebSearchApplication(ChatCompletion):
    def __init__(self):
        self.tools = [
            CalculationsAgentTool(endpoint=DIAL_ENDPOINT),
            ContentManagementAgentTool(endpoint=DIAL_ENDPOINT)
        ]
        self.mcp_tools_created = False

    async def _get_websearch_tools(self) -> list[BaseTool]:
        mcp_client = MCPClient(mcp_server_url=_DDG_MCP_URL)
        mcp_tools = []
        for tool in await mcp_client.get_tools():
            mcp_tools.append(
                MCPTool(
                    client=mcp_client,
                    mcp_tool_model=tool
                )
            )
        return mcp_tools
    
    async def chat_completion(self, request: Request, response: Response) -> None:
        if not self.mcp_tools_created:
            mcp_tools = await self._get_websearch_tools()
            self.tools.extend(mcp_tools)
            self.mcp_tools_created = True

        with response.create_single_choice() as choice:
            await WebSearchAgent(
                endpoint=DIAL_ENDPOINT,
                tools=self.tools
            ).handle_request(
                choice=choice,
                deployment_name=DEPLOYMENT_NAME,
                request=request,
                response=response,
            )

app = DIALApp()
web_search_app = WebSearchApplication()
app.add_chat_completion(deployment_name="web-search-agent", impl=web_search_app)
uvicorn.run(app, host="0.0.0.0", port=5003)