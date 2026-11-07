"""Batch model tokens without delaying tool status or the final fragment."""
import asyncio
import os
import queue
import threading
import time


def buffer_interval():
    try:
        return max(0.05, min(2.0, float(os.environ.get('STREAM_BUFFER_MS', '350')) / 1000))
    except ValueError:
        return 0.35


async def buffered_events(source, interval=None):
    interval = buffer_interval() if interval is None else interval
    events = queue.Queue(maxsize=64)
    stopped = threading.Event()
    end = object()

    def put(item):
        while not stopped.is_set():
            try:
                events.put(item, timeout=0.1)
                return
            except queue.Full:
                pass

    def produce():
        try:
            for event in source:
                if stopped.is_set():
                    break
                put((event, None))
        except Exception as error:
            put((None, error))
        finally:
            put((end, None))

    threading.Thread(target=produce, daemon=True, name='agent-stream').start()
    parts = []
    deadline = None
    try:
        while True:
            timeout = max(0, deadline - time.monotonic()) if deadline else 0.25
            try:
                event, error = await asyncio.to_thread(events.get, True, timeout)
            except queue.Empty:
                if parts:
                    yield {'text': ''.join(parts)}
                    parts = []
                    deadline = None
                continue
            if error:
                raise error
            if event is end:
                if parts:
                    yield {'text': ''.join(parts)}
                break
            if 'text' in event:
                if not parts:
                    deadline = time.monotonic() + interval
                parts.append(event['text'])
            else:
                if parts:
                    yield {'text': ''.join(parts)}
                    parts = []
                    deadline = None
                yield event
            if deadline and time.monotonic() >= deadline:
                yield {'text': ''.join(parts)}
                parts = []
                deadline = None
    finally:
        stopped.set()
