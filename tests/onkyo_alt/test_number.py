"""Tests de la plateforme number propre à onkyo_alt (amélioration des dialogues, VOC)."""

import asyncio
from collections.abc import AsyncGenerator
from datetime import timedelta
from unittest.mock import AsyncMock, patch

from aioonkyo_alt import Code, Instruction, Kind, Zone, command, query, status
from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant.common import MockConfigEntry, async_fire_time_changed

from custom_components.onkyo_alt.coordinator import POWER_ON_QUERY_DELAY
from homeassistant.components.number import (
    ATTR_VALUE,
    DOMAIN as NUMBER_DOMAIN,
    SERVICE_SET_VALUE,
)
from homeassistant.const import ATTR_ENTITY_ID, STATE_UNAVAILABLE, STATE_UNKNOWN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import DISCONNECT, receive_messages, setup_integration

# L'entité number n'est rattachée à aucun appareil (comme les entités du cœur) et
# n'a pas de préfixe de modèle dans son nom : son entity_id est donc court.
ENTITY_ID = "number.dialog_enhancement"
CODE = Code.from_kind_zone(Kind.DIALOG_ENHANCEMENT, Zone.MAIN)


def _voc(value: int) -> status.DialogEnhancement:
    """Message VOC renvoyé par l'ampli."""
    return status.DialogEnhancement(CODE, None, value)


@pytest.fixture
async def setup_number(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_config_entry: MockConfigEntry,
    mock_receiver: AsyncMock,
    writes: list[Instruction],
) -> AsyncGenerator[None]:
    """Configure l'intégration avec la seule plateforme number."""
    with patch("custom_components.onkyo_alt.PLATFORMS", [Platform.NUMBER]):
        await setup_integration(hass, mock_config_entry)
        freezer.tick(timedelta(seconds=POWER_ON_QUERY_DELAY))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        yield


@pytest.mark.usefixtures("setup_number")
async def test_queried_on_connect_and_created_on_first_answer(
    hass: HomeAssistant,
    read_queue: asyncio.Queue,
    writes: list[Instruction],
    entity_registry: er.EntityRegistry,
) -> None:
    """La valeur est demandée à la connexion ; l'entité n'existe qu'après la réponse."""
    assert query.DialogEnhancement() in writes
    assert hass.states.get(ENTITY_ID) is None

    await receive_messages(read_queue, _voc(3))
    await hass.async_block_till_done()

    assert (state := hass.states.get(ENTITY_ID)) is not None
    assert float(state.state) == 3
    assert (entry := entity_registry.async_get(ENTITY_ID)) is not None
    assert entry.unique_id == "0009B0123456-dialog_enhancement"


@pytest.mark.usefixtures("setup_number")
async def test_not_available_answer(
    hass: HomeAssistant, read_queue: asyncio.Queue
) -> None:
    """Une réponse N/A crée l'entité, indisponible (comportement actuel du coordinateur)."""
    assert hass.states.get(ENTITY_ID) is None

    await receive_messages(
        read_queue, status.NotAvailable(CODE, None, Kind.DIALOG_ENHANCEMENT)
    )
    await hass.async_block_till_done()

    assert (state := hass.states.get(ENTITY_ID)) is not None
    assert state.state == STATE_UNAVAILABLE


@pytest.mark.usefixtures("setup_number")
async def test_set_value_and_availability(
    hass: HomeAssistant, read_queue: asyncio.Queue, writes: list[Instruction]
) -> None:
    """Réglage de la valeur, puis indisponibilité à la déconnexion."""
    await receive_messages(read_queue, _voc(1))
    await hass.async_block_till_done()
    writes.clear()

    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_VALUE: 4},
        blocking=True,
    )
    assert writes == [command.DialogEnhancement(4)]

    await receive_messages(read_queue, _voc(4))
    await hass.async_block_till_done()
    assert (state := hass.states.get(ENTITY_ID)) is not None
    assert float(state.state) == 4

    await receive_messages(
        read_queue, status.NotAvailable(CODE, None, Kind.DIALOG_ENHANCEMENT)
    )
    await hass.async_block_till_done()
    assert (state := hass.states.get(ENTITY_ID)) is not None
    assert state.state == STATE_UNAVAILABLE

    await receive_messages(read_queue, _voc(2), DISCONNECT)
    await hass.async_block_till_done()
    assert (state := hass.states.get(ENTITY_ID)) is not None
    assert state.state == STATE_UNAVAILABLE
    assert state.state != STATE_UNKNOWN
