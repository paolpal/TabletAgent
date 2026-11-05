"""Small MCP server used only for local adapter integration tests."""
from fastmcp import FastMCP

server = FastMCP('tablet-agent-test')


@server.tool
def greeting(name: str) -> str:
    """Return a greeting for a name."""
    return 'Ciao ' + name


app = server.http_app(path='/mcp')
