import asyncio
import websockets
import os
import json

# Un diccionario donde cada clave es el nombre/ID de la sala
# y el valor es el estado de esa sala
salas = {}

def check_winner(state):
    lines = [
        (0,1,2), (3,4,5), (6,7,8),
        (0,3,6), (1,4,7), (2,5,8),
        (0,4,8), (2,4,6)
    ]
    for a,b,c in lines:
        if state[a] and state[a] == state[b] == state[c]:
            return state[a]
    if all(state):
        return "Empate"
    return None

async def handler(ws):
    room = None
    symbol = None
    try:
        async for message in ws:
            data = json.loads(message)

            # 1. JOIN ROOM
            if data.get("type") == "join":
                room = data.get("room")
                if not room:
                    await ws.send(json.dumps({ "type": "error", "msg": "Sin sala" }))
                    return
                if room not in salas:
                    salas[room] = {
                        "clients": [],
                        "state": [""] * 9,
                        "turn": "X",
                        "game_over": False
                    }
                sala = salas[room]
                if len(sala["clients"]) >= 2:
                    await ws.send(json.dumps({ "type": "full" }))
                    return
                symbol = "X" if not sala["clients"] else "O"
                sala["clients"].append({"ws": ws, "symbol": symbol})
                await ws.send(json.dumps({ "type": "init", "symbol": symbol }))
                # Estado inicial para todos los jugadores de la sala
                for c in sala["clients"]:
                    await c["ws"].send(json.dumps({
                        "type": "state",
                        "state": sala["state"],
                        "turn": sala["turn"]
                    }))
                continue

            # 2. SOLO SI YA ESTÁ EN UNA SALA
            if not room or room not in salas:
                await ws.send(json.dumps({ "type": "error", "msg": "No unido a una sala" }))
                continue
            sala = salas[room]

            # 3. MOVIMIENTO
            if data.get("type") == "move" and not sala["game_over"]:
                idx = data["index"]
                if sala["state"][idx] == "" and sala["turn"] == symbol:
                    sala["state"][idx] = symbol
                    winner = check_winner(sala["state"])
                    if winner == "Empate":
                        for c in sala["clients"]:
                            await c["ws"].send(json.dumps({
                                "type": "end", "state": sala["state"], "winner": None
                            }))
                        sala["game_over"] = True
                    elif winner:
                        for c in sala["clients"]:
                            await c["ws"].send(json.dumps({
                                "type": "end", "state": sala["state"], "winner": winner
                            }))
                        sala["game_over"] = True
                    else:
                        sala["turn"] = "O" if sala["turn"] == "X" else "X"
                        for c in sala["clients"]:
                            await c["ws"].send(json.dumps({
                                "type": "state",
                                "state": sala["state"],
                                "turn": sala["turn"]
                            }))

    except:
        pass
    finally:
        # Al desconectarse, quitar jugador de la sala y resetear si es necesario
        if room and room in salas:
            sala = salas[room]
            sala["clients"] = [c for c in sala["clients"] if c["ws"] != ws]
            if not sala["clients"]:
                del salas[room]  # borra sala si se va el último

port = int(os.environ.get("PORT", 10000))
start_server = websockets.serve(handler, "0.0.0.0", port)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
