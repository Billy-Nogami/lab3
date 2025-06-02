import httpx
import websockets
import asyncio
import uuid
import json

async def main():
    url = input("Введите URL для парсинга: ")
    client_id = str(uuid.uuid4())
    print(f"Ваш client_id: {client_id}")

    # 1. Устанавливаем WebSocket соединение
    print("Устанавливаем WebSocket соединение...")
    async with websockets.connect(f"ws://localhost:8000/ws/{client_id}") as websocket:
        print("WebSocket подключен. Проверяем соединение...")
        
        # 2. Проверяем работоспособность соединения
        try:
            # Отправляем тестовое сообщение
            await websocket.send("TEST_CONNECTION")
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            
            if response == "CONNECTION_OK":
                print("Соединение проверено и работает корректно.")
            else:
                print(f"Неожиданный ответ от сервера: {response}")
                return
        except asyncio.TimeoutError:
            print("Таймаут при проверке соединения. Сервер не отвечает.")
            return
        except websockets.exceptions.ConnectionClosed:
            print("Соединение закрыто сервером во время проверки.")
            return
        
        # 3. Только после проверки соединения отправляем задачу
        print("Отправляем задачу на парсинг...")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/parse-url",
                json={"url": url, "client_id": client_id}
            )
            task_info = response.json()
            print("Задача отправлена:", task_info)
            print(f"ID задачи: {task_info['id']}")
        
        # 4. Ожидаем результат
        print("Ожидаем результат...")
        try:
            while True:
                message = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                if "Task" in message and str(task_info['id']) in message:
                    print("Ответ от сервера:", message)
                    break
                else:
                    print(f"Получено промежуточное сообщение: {message}")
        except asyncio.TimeoutError:
            print("Таймаут: результат не получен в течение 60 секунд")
        except websockets.exceptions.ConnectionClosed:
            print("Соединение закрыто сервером до получения результата")

if __name__ == "__main__":
    asyncio.run(main())