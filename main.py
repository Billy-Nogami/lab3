from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.api import parse
from app.websocket.manager import manager
import asyncio
import redis.asyncio as redis
from app.core.config import settings
import json

app = FastAPI()
app.include_router(parse.router)


@app.on_event("startup")
async def startup_event():
    # Подключение к Redis и запуск слушателя
    r = redis.Redis.from_url(settings.REDIS_URL)
    pubsub = r.pubsub()

    # Подписываемся только на каналы, начинающиеся с "ws:"
    await pubsub.psubscribe("ws:*")

    async def redis_listener():
        print("Redis listener task started")
        async for message in pubsub.listen():
            if message["type"] == "pmessage":
                try:
                    # Извлекаем client_id из шаблона канала (ws:client_id)
                    pattern = message["pattern"].decode()
                    channel = message["channel"].decode()

                    # Проверяем, что это наш канал
                    if pattern == "ws:*":
                        # Извлекаем client_id из канала
                        client_id = channel.split(":")[1]
                        data = message["data"].decode()
                        print(f"Received Redis message for {client_id}: {data}")

                        # Отправляем сообщение клиенту
                        await manager.send_message(client_id, data)
                    else:
                        print(f"Ignoring non-client message: {channel}")
                except Exception as e:
                    print(f"Ошибка обработки сообщения Redis: {str(e)}")

    asyncio.create_task(redis_listener())


# main.py
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(client_id, websocket)
    print(f"Клиент {client_id} подключен")
    try:
        while True:
            # Ожидаем сообщения от клиента
            data = await websocket.receive_text()
            print(f"Получено от клиента {client_id}: {data}")

            # Обработка тестового сообщения
            if data == "TEST_CONNECTION":
                await websocket.send_text("CONNECTION_OK")
                print(f"Подтверждение отправлено клиенту {client_id}")

    except WebSocketDisconnect:
        print(f"Клиент {client_id} отключился")
        manager.disconnect(client_id)


@app.get("/check-connection/{client_id}")
async def check_connection(client_id: str):
    if client_id in manager.active_connections:
        return {"status": "connected"}
    return {"status": "disconnected"}


@app.get("/active-connections")
async def get_active_connections():
    return {
        "count": len(manager.active_connections),
        "connections": list(manager.active_connections.keys()),
    }
