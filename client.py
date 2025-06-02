import websockets
import asyncio
import uuid
import httpx

async def main():
    client_id = str(uuid.uuid4())
    print(f"Ваш client_id: {client_id}")

    try:
        async with websockets.connect(f"ws://localhost:8000/ws/{client_id}") as websocket:
            print("Устанавливаем WebSocket соединение...")
            print("WebSocket подключен. Проверяем соединение...")
            await websocket.send("TEST_CONNECTION")
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            if response == "CONNECTION_OK":
                print("Соединение проверено и работает корректно.")
            else:
                print(f"Неожиданный ответ от сервера: {response}")
                return

            url = input("Введите URL для парсинга: ")
            async with httpx.AsyncClient() as client:
                print("Отправляем задачу на парсинг...")
                response = await client.post(
                    "http://localhost:8000/parse-url",
                    json={"url": url, "client_id": client_id}
                )
                task_info = response.json()
                print("Задача отправлена:", task_info)
                print(f"ID задачи: {task_info['id']}")

            print("Ожидаем результат...")
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                    if message == "ping":
                        print("Получен ping от сервера")
                    elif "Task" in message and str(task_info['id']) in message:
                        print("Ответ от сервера:", message)
                        break
                    else:
                        print(f"Получено промежуточное сообщение: {message}")
                except asyncio.TimeoutError:
                    print("Таймаут: результат не получен в течение 60 секунд")
                    break
                except websockets.exceptions.ConnectionClosed:
                    print("Соединение закрыто сервером")
                    break
                except Exception as e:
                    print(f"Ошибка при получении сообщения: {e}")
                    break
    except Exception as e:
        print(f"Ошибка при подключении к WebSocket: {e}")

if __name__ == "__main__":
    asyncio.run(main())