"""Experiments: MCP discovery, invocation and Deep Agents interoperability."""
import asyncio
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
from deepagents import create_deep_agent
from fastmcp import FastMCP
from langchain.mcp import MCPAdapter
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, ToolMessage


class ToolCallingModel(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


def test_in_process_mcp_tool_used_by_deep_agent():
    server = FastMCP('test')

    @server.tool
    def greeting(name: str) -> str:
        """Return a greeting for a name."""
        return 'Ciao ' + name

    async def exercise():
        async with MCPAdapter(server) as adapter:
            tools = await adapter.list_tools()
            assert [tool.name for tool in tools] == ['greeting']
            with pytest.raises(NotImplementedError):
                tools[0].invoke({'name': 'Tablet'})
            model = ToolCallingModel(responses=[
                AIMessage(content='', tool_calls=[{'name': 'greeting', 'args': {'name': 'Tablet'}, 'id': 'call-1'}]),
                AIMessage(content='Risposta completata'),
            ])
            agent = create_deep_agent(model=model, tools=tools)
            states = []
            async for state in agent.astream({'messages': [{'role': 'user', 'content': 'Saluta Tablet'}]}, stream_mode='values'):
                states.append(state)
            result = states[-1]
            tool_result = [message for message in result['messages'] if isinstance(message, ToolMessage)]
            assert len(tool_result) == 1
            assert 'Ciao Tablet' in str(tool_result[0].content)
            assert result['messages'][-1].content == 'Risposta completata'

    asyncio.run(exercise())


def test_http_mcp_server_discovery_and_call():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    fixture = Path(__file__).parent / 'fixtures'
    process = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'mcp_server:app', '--host', '127.0.0.1', '--port', str(port)],
        cwd=fixture, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(100):
            if process.poll() is not None:
                raise AssertionError('MCP test server exited')
            try:
                with socket.create_connection(('127.0.0.1', port), timeout=.1):
                    break
            except OSError:
                time.sleep(.05)
        else:
            raise AssertionError('MCP test server did not start')

        async def exercise():
            async with MCPAdapter('http://127.0.0.1:%s/mcp' % port) as adapter:
                tools = await adapter.list_tools()
                assert [tool.name for tool in tools] == ['greeting']
                result = await tools[0].ainvoke({'name': 'Tablet'})
                assert 'Ciao Tablet' in str(result)

        asyncio.run(exercise())
    finally:
        process.terminate()
        process.wait(timeout=10)
