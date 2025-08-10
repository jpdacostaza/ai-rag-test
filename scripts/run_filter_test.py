import sys, os, asyncio
sys.path.append(os.getcwd())
from memory.functions.auto_web_search_filter import Filter

async def main():
    f = Filter()
    body = {"messages": [{"role": "user", "content": "search the web for the latest technology news about AI today"}]}
    new_body = await f.inlet(body)
    print('Total messages:', len(new_body['messages']))
    for i,m in enumerate(new_body['messages']):
        print(f"{i}:{m['role']} => {m['content'][:140].replace('\n',' ')}")

if __name__ == '__main__':
    asyncio.run(main())
