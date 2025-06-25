import asyncio
import websockets
import os

clientes = set()

async def handler(websocket):
    clientes.add(websocket)
    try:
        async for mensaje in websocket:
            for cliente in clientes:
                if cliente != websocket:
                    await cliente.send(mensaje)
    except:
        pass
    finally:
        clientes.remove(websocket)

async def main():
    puerto = int(os.environ.get("PORT", 10000))
    async with websockets.serve(handler, "0.0.0.0", puerto):
        print(f"Servidor WebSocket activo en el puerto {puerto}")
        await asyncio.Future()

asyncio.run(main())
