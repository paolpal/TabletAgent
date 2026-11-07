import asyncio
import time

from app.stream_buffer import buffered_events


def test_batches_tokens_preserves_status_and_flushes_final_text():
    async def collect():
        source = iter([{'text': 'a'}, {'text': 'b'}, {'status': 'Cerco'}, {'text': 'c'}])
        return [event async for event in buffered_events(source, interval=1)]

    assert asyncio.run(collect()) == [{'text': 'ab'}, {'status': 'Cerco'}, {'text': 'c'}]


def test_flushes_text_even_if_model_pauses():
    def source():
        yield {'text': 'primo'}
        time.sleep(.3)
        yield {'text': 'secondo'}

    async def collect():
        start = time.monotonic()
        output = []
        async for event in buffered_events(source(), interval=.05):
            output.append((event, time.monotonic() - start))
        return output

    output = asyncio.run(collect())
    assert output[0][0] == {'text': 'primo'}
    assert output[0][1] < .25
    assert output[1][0] == {'text': 'secondo'}
