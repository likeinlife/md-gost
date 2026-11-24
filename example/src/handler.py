"""Пример исходного файла, из которого вставляется листинг."""

import json


def handle(request):
    """Разбирает тело запроса и возвращает ответ."""
    payload = json.loads(request.body)
    return Response(200, payload)


def health():
    return Response(200, {"status": "ok"})
