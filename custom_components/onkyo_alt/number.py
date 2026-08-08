"""Number platform.

Ajouter un réglage numérique = ajouter une entrée dans NUMBERS ci-dessous,
plus la clé de traduction correspondante dans strings.json / translations.
Aucune classe supplémentaire n'est nécessaire.
"""

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING, cast, override

from aioonkyo_alt import Instruction, Kind, command, query

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import NumericSettingCoordinator

if TYPE_CHECKING:
    from . import OnkyoConfigEntry

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class OnkyoNumberDescription(NumberEntityDescription):
    """Description d'une entité number Onkyo."""

    kind: Kind
    query: Callable[[], Instruction]
    command: Callable[[int], Instruction]


NUMBERS: tuple[OnkyoNumberDescription, ...] = (
    OnkyoNumberDescription(
        key="dialog_enhancement",
        translation_key="dialog_enhancement",
        icon="mdi:account-voice",
        entity_category=EntityCategory.CONFIG,
        mode=NumberMode.SLIDER,
        native_min_value=0,
        native_max_value=5,
        native_step=1,
        kind=Kind.DIALOG_ENHANCEMENT,
        query=query.DialogEnhancement,
        command=command.DialogEnhancement,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OnkyoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up number platform for config entry."""

    @callback
    def async_add_number(coordinator: NumericSettingCoordinator) -> None:
        """Add the entity once the receiver has proven it supports the setting."""
        async_add_entities([OnkyoNumber(coordinator)])

    # Les coordinateurs sont créés ici, et non dans __init__.py : la plateforme
    # est configurée avant manager.start(), donc leurs callbacks sont enregistrés
    # à temps pour la requête émise à l'ouverture de la connexion.
    for description in NUMBERS:
        NumericSettingCoordinator(
            hass,
            entry,
            entry.runtime_data.manager,
            description,
            async_add_number,
        )


class OnkyoNumber(CoordinatorEntity[NumericSettingCoordinator], NumberEntity):
    """Numeric setting of an Onkyo receiver."""

    _attr_has_entity_name = True

    entity_description: OnkyoNumberDescription

    def __init__(self, coordinator: NumericSettingCoordinator) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)

        description = cast(OnkyoNumberDescription, coordinator.description)
        self.entity_description = description

        identifier = coordinator.manager.info.identifier
        self._attr_unique_id = f"{identifier}-{description.key}"

    @property
    @override
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.manager.connected and self.coordinator.data is not None

    @property
    @override
    def native_value(self) -> float | None:
        """Return the current value.

        Lu directement depuis le coordinateur plutôt que mis en cache dans
        _attr_native_value : l'entité est ajoutée pendant le traitement du tout
        premier message, donc son listener n'est pas encore enregistré quand
        async_set_updated_data() suit. Un cache alimenté par
        _handle_coordinator_update() raterait cette première valeur et l'entité
        resterait "unknown" jusqu'au message suivant.
        """
        value = self.coordinator.data
        return None if value is None else float(value)

    @override
    async def async_set_native_value(self, value: float) -> None:
        """Set the value on the receiver."""
        await self.coordinator.async_send_command(int(value))
