"""Small stdio test client for the installed command and the source-tree server."""

import json
import os
import subprocess
import sys
from collections.abc import Generator
from contextlib import ExitStack, contextmanager
from itertools import count
from pathlib import Path
from queue import Queue
from threading import Thread
from typing import IO, Any

Message = dict[str, Any]
TIMEOUT = 10
DIAGNOSTICS = "textDocument/publishDiagnostics"
ARGUMENT_FIELD = "params"
ID = "id"
METHOD = "method"


def _read_messages(stream: IO[bytes], inbox: Queue[Message | None]) -> None:
    size = 0
    for header in stream:
        if header.lower().startswith(b"content-length:"):
            size = int(header.partition(b":")[2])
        elif not header.strip():
            inbox.put(json.loads(stream.read(size)))
    inbox.put(None)


class Client:
    def __init__(self, stream: IO[bytes], inbox: Queue[Message | None]) -> None:
        self.stream = stream
        self.inbox = inbox
        self.ids = count(1)

    def notify(self, method: str, arguments: Message) -> None:
        self._send({METHOD: method, ARGUMENT_FIELD: arguments})

    def request(self, method: str, arguments: Message | None = None) -> Any:
        sequence = next(self.ids)
        self._send({ID: sequence, METHOD: method, ARGUMENT_FIELD: arguments})
        while True:
            packet = self._receive()
            assert ID not in packet or METHOD not in packet, packet
            if packet.get(ID) == sequence:
                assert "error" not in packet, packet
                return packet["result"]

    def answer(self, method: str, reply: Message) -> Message:
        while True:
            packet = self._receive()
            sequence = packet.get(ID)
            if sequence is not None:
                assert packet.get(METHOD) == method, packet
                self._send({ID: sequence, "result": reply})
                return packet[ARGUMENT_FIELD]

    def diagnostics(self, uri: str) -> list[Message]:
        while True:
            packet = self._receive()
            if packet.get(METHOD) == DIAGNOSTICS:
                report = packet[ARGUMENT_FIELD]
                if report["uri"] == uri:
                    return report["diagnostics"]

    def _send(self, packet: Message) -> None:
        payload = json.dumps({"jsonrpc": "2.0", **packet}).encode()
        self.stream.write(f"Content-Length: {len(payload)}\r\n\r\n".encode())
        self.stream.write(payload)
        self.stream.flush()

    def _receive(self) -> Message:
        packet = self.inbox.get(timeout=TIMEOUT)
        assert packet is not None, "LSP server closed stdout before replying"
        return packet


def _command() -> list[str]:
    executable = os.environ.get("MD_GOST_LSP_EXECUTABLE")
    script = Path(__file__).resolve().parents[1] / "gost_server.py"
    return [executable] if executable else [sys.executable, str(script)]


@contextmanager
def start_client(directory: Path) -> Generator[Client, None, None]:
    with subprocess.Popen(
        _command(),
        cwd=directory,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    ) as proc:
        assert proc.stdout is not None
        assert proc.stdin is not None
        inbox: Queue[Message | None] = Queue()
        Thread(target=_read_messages, args=(proc.stdout, inbox), daemon=True).start()
        with ExitStack() as cleanup:
            cleanup.callback(proc.kill)
            yield Client(proc.stdin, inbox)
            assert proc.wait(timeout=TIMEOUT) == 0


@contextmanager
def initialized_client(folder: Path, capabilities: Message) -> Generator[Client, None, None]:
    with start_client(folder) as connection:
        response = connection.request(
            "initialize",
            {"rootUri": folder.as_uri(), "capabilities": capabilities},
        )
        assert "capabilities" in response
        connection.notify("initialized", {})
        yield connection
        assert connection.request("shutdown") is None
        connection.notify("exit", {})


def open_markdown(client: Client, path: Path, source: str, version: int = 1) -> None:
    descriptor = {
        "uri": path.as_uri(),
        "languageId": "markdown",
        "version": version,
        "text": source,
    }
    client.notify("textDocument/didOpen", {"textDocument": descriptor})
