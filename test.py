import asyncio
a = False
async def main():
    await asyncio.sleep(1)
    global a
    a = True
    print('hello')
    
while not a:
    asyncio.run(main())
    pass
print('done')
