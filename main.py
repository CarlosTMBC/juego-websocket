import asyncio
import websockets
import os
import json

clients = []
state = [""] * 9
turn = "X"
game_over = False

def check_winner():
    lines = [
        (0,1,2), (3,4,5), (6,7,8), # filas
        (0,3,6), (1,4,7), (2,5,8), # columnas
        (0,4,8), (2,4,6)           # diagonales
    ]
    for a,b,c in lines:
        if state[a] and state[a] == state[b] == state[c]:
            return state[a]
    if all(state):
        return "Empate"
    return None

async def notify_all(message):
    for client in clients:
        await client["ws"].send(json.dumps(message))

async def handler(ws):
    global turn, state, game_over

    if len(clients) >= 2:
        await ws.send(json.dumps({ "type": "full" }))
        return

    symbol = "X" if not clients else "O"
    client = { "ws": ws, "symbol": symbol }
    clients.append(client)

    await ws.send(json.dumps({ "type": "init", "symbol": symbol }))
    await notify_all({ "type": "state", "state": state, "turn": turn })

    try:
        async for message in ws:
            data = json.loads(message)
            if data["type"] == "move" and not game_over:
                idx = data["index"]
                if state[idx] == "" and turn == client["symbol"]:
                    state[idx] = client["symbol"]
                    winner = check_winner()
                    if winner == "Empate":
                        await notify_all({ "type": "end", "state": state, "winner": None })
                        game_over = True
                    elif winner:
                        await notify_all({ "type": "end", "state": state, "winner": winner })
                        game_over = True
                    else:
                        turn = "O" if turn == "X" else "X"
                        await notify_all({ "type": "state", "state": state, "turn": turn })
    except:
        pass
    finally:
        clients.remove(client)
        if len(clients) < 2:
            # Reset juego si un jugador se desconecta
            state = [""] * 9
            turn = "X"
            game_over = False

port = int(os.environ.get("PORT", 10000))
start_server = websockets.serve(handler, "0.0.0.0", port)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
