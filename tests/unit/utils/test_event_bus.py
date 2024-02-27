import unittest

import pytest
from unittest.mock import Mock
from utils.event_bus import EventBus


def test_event_bus_subscribes_handlers_correctly():
    event_bus = EventBus()
    handler = Mock()

    event_bus.subscribe('test_event', handler)
    assert 'test_event' in event_bus.subscribers
    assert handler in event_bus.subscribers['test_event']


def test_event_bus_publishes_events_to_subscribers():
    event_bus = EventBus()
    handler = Mock()

    event_bus.subscribe('test_event', handler)
    event_bus.publish('test_event', 42, key='value')

    handler.assert_called_once_with(42, key='value')


def test_event_bus_does_not_call_handlers_for_other_events():
    event_bus = EventBus()
    handler = Mock()

    event_bus.subscribe('test_event', handler)
    event_bus.publish('other_event', 42, key='value')

    handler.assert_not_called()


@pytest.mark.asyncio
async def test_event_bus_with_async_handlers():
    event_bus = EventBus()
    async_handler = Mock()

    event_bus.subscribe('async_event', async_handler)
    event_bus.publish('async_event', 'async', key='test')

    async_handler.assert_called_once_with('async', key='test')

if __name__ == '__main__':
    unittest.main()
