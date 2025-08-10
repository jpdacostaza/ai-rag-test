import asyncio
from memory.functions.auto_web_search_filter import Filter

async def main():
    f = Filter()
    body = {"messages": [{"role": "user", "content": "search the web for today's latest technology news about AI"}]}
    new_body = await f.inlet(body)
    for m in new_body["messages"]:
        print(m["role"], "::", m["content"][:120].replace("\n", " ") + ("..." if len(m["content"])>120 else ""))

if __name__ == '__main__':
    asyncio.run(main())
