import asyncio
import click
from mcp.client.session import ClientSession

from mcp.client.sse import sse_client


async def __main(endpoint: str):
    async with sse_client(
        url=endpoint,
        headers={"Authorization": "Bearer test-user-id"},
    ) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print(tools)

            # Call the execute_command tool
            result = await session.call_tool("hello", {})
            print("-" * 100)
            for content in result.content:
                print(content.text)


@click.command()
@click.option("--endpoint", default="http://localhost:8000/sse", help="URL of the SSE endpoint")
def main(endpoint: str):
    asyncio.run(__main(endpoint))


if __name__ == "__main__":
    main()
