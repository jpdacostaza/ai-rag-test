import asyncio, aiohttp, json, textwrap

QUERIES = [
    "OpenWebUI function call not executing tool",
    "OpenWebUI Action class web_search not called",
    "OpenWebUI No Function class found in the module fix",
    "OpenWebUI tools function calling qwen",
    "OpenWebUI function calling template TOOLS_FUNCTION_CALLING_PROMPT_TEMPLATE"
]

URL = "http://localhost:3000/tools/web_search"

async def do_query(session, q):
    async with session.post(URL, json={"query": q}) as resp:
        txt = await resp.text()
        try:
            data = json.loads(txt)
        except Exception:
            print(f"[PARSE FAIL] {q}\n{txt[:400]}\n")
            return []
        results = data.get("results", "")
        # crude split by double newline on **n. pattern
        lines = [l for l in results.splitlines() if l.strip() and l.strip().startswith("**")]  # titles
        cleaned = []
        for l in lines[:5]:
            title = l.strip('* ').split('**')[0]
            cleaned.append(title)
        return cleaned

async def main():
    async with aiohttp.ClientSession() as session:
        for q in QUERIES:
            try:
                titles = await do_query(session, q)
                print(f"QUERY: {q}")
                if not titles:
                    print("  (no titles parsed)")
                else:
                    for i,t in enumerate(titles,1):
                        print(f"  {i}. {t}")
                print()
            except Exception as e:
                print(f"QUERY ERROR {q}: {e}")

if __name__ == '__main__':
    asyncio.run(main())
