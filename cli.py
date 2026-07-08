import asyncio
import websockets
import json
import sys

async def chat():
    uri = "ws://localhost:8000/ws/chat"
    try:
        async with websockets.connect(uri) as websocket:
            msg = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Hello! Can you list the files in the current directory?"
            print(f"> {msg}")
            await websocket.send(json.dumps({"message": msg}))
            
            while True:
                try:
                    response = await websocket.recv()
                    data = json.loads(response)
                    if data["type"] == "response_chunk":
                        print(data["data"]["content"], end="", flush=True)
                    elif data["type"] == "tool_call":
                        tc = data["data"]["tool_call"]["function"]
                        print(f"\n[Tool Call] {tc['name']}({tc['arguments']})", flush=True)
                    elif data["type"] == "tool_result":
                        print(f"\n[Tool Result] {data['data']['result'][:200]}...", flush=True)
                    elif data["type"] in ("done", "error"):
                        if data["type"] == "error":
                            print(f"\n[Error] {data['data']['error']}", flush=True)
                        print("\n[Done]")
                        break
                except websockets.exceptions.ConnectionClosed:
                    print("\n[Connection Closed]")
                    break
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    asyncio.run(chat())
