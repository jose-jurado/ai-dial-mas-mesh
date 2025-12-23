import os

import uvicorn
from aidial_sdk import DIALApp
from aidial_sdk.chat_completion import ChatCompletion, Request, Response

from task.agents.calculations.calculations_agent import CalculationsAgent
from task.agents.calculations.tools.simple_calculator_tool import SimpleCalculatorTool
from task.tools.base_tool import BaseTool
from task.agents.calculations.tools.py_interpreter.python_code_interpreter_tool import PythonCodeInterpreterTool
from task.tools.mcp.mcp_client import MCPClient
from task.tools.deployment.content_management_agent_tool import ContentManagementAgentTool
from task.tools.deployment.web_search_agent_tool import WebSearchAgentTool
from task.tools.mcp.mcp_tool import MCPTool
from task.utils.constants import DIAL_ENDPOINT, DEPLOYMENT_NAME


_PYTHON_INTERPRETER_MCP_URL = os.getenv("PYINTERPRETER_MCP_URL", "http://localhost:8050/mcp")

# 1. Create CalculationsApplication class and extend ChatCompletion
# 2. As a tools for CalculationsAgent you need to provide:
#   - SimpleCalculatorTool
#   - PythonCodeInterpreterTool
#   - ContentManagementAgentTool (MAS Mesh)
#   - WebSearchAgentTool (MAS Mesh)
# 3. Override the chat_completion method of ChatCompletion, create Choice and call CalculationsAgent
# ---
# 4. Create DIALApp with deployment_name `calculations-agent` (the same as in the core config) and impl is instance of
#    the CalculationsApplication
# 5. Add starter with DIALApp, port is 5001 (see core config)

class CalculationsApplication(ChatCompletion):
    def __init__(self):
        self.tools = [
            SimpleCalculatorTool(),
            ContentManagementAgentTool(endpoint=DIAL_ENDPOINT),
            WebSearchAgentTool(endpoint=DIAL_ENDPOINT)
        ]
        self.mcp_tools_created = False

    async def _get_interpreter_tool(self) -> PythonCodeInterpreterTool:
        mcp_client = MCPClient(mcp_server_url=_PYTHON_INTERPRETER_MCP_URL)
        mcp_tools = []
        for tool in await mcp_client.get_tools():
            mcp_tools.append(
                MCPTool(
                    client=mcp_client,
                    mcp_tool_model=tool
                )
            )

        return PythonCodeInterpreterTool(
                mcp_client=mcp_client,
                mcp_tool_models=mcp_tools,
                tool_name="python_code_interpreter",
                dial_endpoint=DIAL_ENDPOINT)
    
    async def chat_completion(self, request: Request, response: Response) -> None:
        if not self.mcp_tools_created:
            interpreter_tool = await self._get_interpreter_tool()
            self.tools.append(interpreter_tool)
            self.mcp_tools_created = True

        with response.create_single_choice() as choice:
            await CalculationsAgent(
                endpoint=DIAL_ENDPOINT,
                tools=self.tools
            ).handle_request(
                choice=choice,
                deployment_name=DEPLOYMENT_NAME,
                request=request,
                response=response,
            )

app = DIALApp()
calculations_app = CalculationsApplication()
app.add_chat_completion(deployment_name="calculations-agent", impl=calculations_app)
uvicorn.run(app, host="0.0.0.0", port=5001)