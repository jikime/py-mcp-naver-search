import asyncio
import sys
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import Any, Dict, List

async def run_search(category: str, query: str, **kwargs: Any) -> None:
    """지정된 카테고리와 파라미터로 MCP 서버의 검색 Tool을 호출하고 결과와 프롬프트를 출력합니다."""

    # 서버 실행 설정: 현재 디렉토리의 server.py를 python으로 실행
    server_params = StdioServerParameters(
        command=sys.executable, # 현재 사용 중인 파이썬 인터프리터 사용
        args=["server.py"],
        env=None,
    )

    # 호출할 Tool 이름 결정
    if category in ["adult", "errata"]:
        tool_name = f"check_{category}_query" if category == "adult" else f"correct_{category}"
    else:
        tool_name = f"search_{category}"

    # Tool 호출 인자 구성 (kwargs에서 필요한 파라미터 추출)
    arguments: Dict[str, Any] = {"query": query}
    if 'display' in kwargs: arguments['display'] = kwargs['display']
    # page 파라미터로 통일
    if 'page' in kwargs: arguments['page'] = kwargs['page']
    if 'sort' in kwargs: arguments['sort'] = kwargs['sort']
    if 'filter' in kwargs: arguments['filter'] = kwargs['filter']

    print(f"--- MCP 서버({category}) 검색 요청 ---")
    print(f"   Tool: {tool_name}, Arguments: {arguments}")

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()
                print("Connection initialized")
                
                # List available resources
                resources = await session.list_resources()
                # print(f"Available resources: {resources}")

                # Get available search categories resource
                try:
                    available_categories = await session.read_resource("naver://available-search-categories")
                    # print(f"Available categories: {available_categories}")
                except Exception as e:
                    print(f"Warning: Could not fetch available categories: {e}")

                # 사용 가능한 툴 목록 가져오기
                tools_info = await session.list_tools()
                # print(f"Available tools info: {tools_info}")
                
                # Tool 객체에서 이름만 추출
                available_tools = []
                if hasattr(tools_info, 'tools'):
                    available_tools = [tool.name for tool in tools_info.tools]
                    # print(f"Available tool names: {available_tools}")
                
                if tool_name not in available_tools:
                    raise ValueError(f"오류: 서버에서 '{tool_name}' Tool을 찾을 수 없습니다. 사용 가능한 Tool: {available_tools}")

                print(f"'{tool_name}' Tool 호출 중...")
                result = await session.call_tool(tool_name, arguments=arguments)
                print(f"Tool 호출 결과: {result}")

                # 결과 출력
                if hasattr(result, 'content'):
                    print("\n--- 검색 결과 ---")
                    print(result.content[0].text)
                else:
                    print("\n--- 예상치 못한 응답 ---")
                    print(result)

    except Exception as e:
        print(f"\n--- 클라이언트 오류 발생 ---")
        print(f"오류 유형: {type(e).__name__}")
        print(f"오류 메시지: {e}")
        if hasattr(e, '__context__') and e.__context__:
            print(f"원인: {e.__context__}")

if __name__ == "__main__":
    # 터미널 인자 파싱 (key=value 형태로 변경)
    if len(sys.argv) < 3:
        print("사용법: uv run client.py <category> <query> [param1=value1] [param2=value2] ...")
        print("   <category>: blog, news, book, adult, encyc, cafe_article, kin, local, errata, shop, doc, image, webkr 중 하나")
        print("   <query>: 검색어 (띄어쓰기 포함 시 \"따옴표\" 사용)")
        print("   [param=value]: display, page, sort, filter 등 Tool 파라미터")
        print("\n예시:")
        print("   uv run client.py blog \"파이썬 MCP\" display=10 page=1")
        print("   uv run client.py news AI display=5 page=3 sort=date")
        print("   uv run client.py image 고양이 display=20 filter=large sort=sim")
        print("   uv run client.py errata \"tst is good\"")
        sys.exit(1)

    category = sys.argv[1].lower()
    query = sys.argv[2]
    tool_params: Dict[str, Any] = {}

    # 추가 인자 파싱 (key=value)
    if len(sys.argv) > 3:
        for arg in sys.argv[3:]:
            if "=" in arg:
                key, value = arg.split("=", 1)
                # 숫자형 파라미터는 int로 변환 시도
                if key in ['display', 'page'] and value.isdigit():
                    tool_params[key.lower()] = int(value)
                else:
                    tool_params[key.lower()] = value
            else:
                print(f"경고: 잘못된 파라미터 형식 무시됨 - {arg}")

    # 비동기 함수 실행
    asyncio.run(run_search(category, query, **tool_params))
