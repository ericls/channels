import unittest

import pytest
from django.test import override_settings

from channels import DEFAULT_CHANNEL_LAYER
from channels.exceptions import InvalidChannelLayerError
from channels.layers import (
    MAX_NAME_LENGTH,
    InMemoryChannelLayer,
    channel_layers,
    get_channel_layer,
)


class TestChannelLayerManager(unittest.TestCase):
    @override_settings(
        CHANNEL_LAYERS={"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
    )
    def test_config_error(self):
        """
        If channel layer doesn't specify TEST_CONFIG, `make_test_backend`
        should result into error.
        """

        with self.assertRaises(InvalidChannelLayerError):
            channel_layers.make_test_backend(DEFAULT_CHANNEL_LAYER)

    @override_settings(
        CHANNEL_LAYERS={
            "default": {
                "BACKEND": "channels.layers.InMemoryChannelLayer",
                "TEST_CONFIG": {"expiry": 100500},
            }
        }
    )
    def test_config_instance(self):
        """
        If channel layer provides TEST_CONFIG, `make_test_backend` should
        return channel layer instance appropriate for testing.
        """

        layer = channel_layers.make_test_backend(DEFAULT_CHANNEL_LAYER)
        self.assertEqual(layer.expiry, 100500)

    def test_override_settings(self):
        """
        The channel layers cache is reset when the CHANNEL_LAYERS setting
        changes.
        """
        with override_settings(
            CHANNEL_LAYERS={
                "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
            }
        ):
            self.assertEqual(channel_layers.backends, {})
            get_channel_layer()
            self.assertNotEqual(channel_layers.backends, {})
        self.assertEqual(channel_layers.backends, {})


### In-memory layer tests


@pytest.mark.asyncio
async def test_send_receive():
    layer = InMemoryChannelLayer()
    message = {"type": "test.message"}
    await layer.send("test.channel", message)
    assert message == await layer.receive("test.channel")


@pytest.mark.parametrize(
    "group_name,expected_valid",
    [("¯\_(ツ)_/¯", False), ("chat", True), ("chat" * 100, False)],
)
def test_valid_group_name(group_name, expected_valid):
    layer = InMemoryChannelLayer()
    if expected_valid:
        layer.valid_group_name(group_name)
    else:
        with pytest.raises(TypeError) as e:
            layer.valid_group_name(group_name)
            assert e.value.message.startswith("Group")
            assert group_name in e.value.message
            assert "< {}".format(MAX_NAME_LENGTH) in e.value.message


@pytest.mark.parametrize(
    "channel_name,expected_valid",
    [("¯\_(ツ)_/¯", False), ("chat", True), ("chat" * 100, False)],
)
def test_valid_channel_name(channel_name, expected_valid):
    layer = InMemoryChannelLayer()
    if expected_valid:
        layer.valid_channel_name(channel_name)
    else:
        with pytest.raises(TypeError) as e:
            layer.valid_channel_name(channel_name)
            assert e.value.message.startswith("Channel")
            assert channel_name in e.value.message
            assert "< {}".format(MAX_NAME_LENGTH) in e.value.message
