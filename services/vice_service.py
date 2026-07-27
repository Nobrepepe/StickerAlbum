import uuid

from models.catalog import Sticker
from models.rarity import STYLES, VICE_VALUES
from models.user_state import ViceOffering
from repositories.user_state_repository import UserStateRepository
from services.errors import ViceError


class ViceService:
    """Explicit spare conversion and point-backed indulgence claims."""

    def __init__(self, state: UserStateRepository):
        self._state = state

    @property
    def points(self) -> int:
        return self._state.state.vice_points

    def spare_count(self, sticker_id: str) -> int:
        return max(0, self._state.total_owned(sticker_id) - 1)

    def conversion_value(self, sticker: Sticker) -> int:
        return VICE_VALUES[sticker.rarity]

    def convert_spares(self, sticker: Sticker, count: int | None = None) -> tuple[int, int]:
        """Convert chosen spares while retaining one usable/applied copy."""
        spare_count = self.spare_count(sticker.id)
        if spare_count < 1:
            raise ViceError(f"{sticker.name} has no spare copies to convert.")
        count = spare_count if count is None else count
        if not isinstance(count, int) or count < 1 or count > spare_count:
            raise ViceError(f"Choose between 1 and {spare_count} spare copies.")

        placement = self._state.get_placement(sticker.id)
        keep_style = placement
        if keep_style is None:
            # Prefer retaining foil when the sticker has not been applied yet.
            keep_style = "foil" if self._state.get_quantity(sticker.id, "foil") else "normal"

        remaining_to_remove = count
        # Consume normal spares first, preserving foil flexibility where
        # possible. The applied copy is always protected regardless of style.
        for style in STYLES:
            quantity = self._state.get_quantity(sticker.id, style)
            removable = min(
                remaining_to_remove,
                quantity - (1 if style == keep_style else 0),
            )
            if removable > 0:
                self._state.remove_copy(sticker.id, style, removable)
                remaining_to_remove -= removable
            if remaining_to_remove == 0:
                break

        earned = count * self.conversion_value(sticker)
        self._state.state.vice_points += earned
        self._state.save()
        return count, earned

    def list_offerings(self) -> list[ViceOffering]:
        return list(self._state.state.vice_offerings)

    def add_offering(
        self, name: str, description: str, price: int, quantity: int
    ) -> ViceOffering:
        offering = self._validated(
            ViceOffering(uuid.uuid4().hex, name, description, price, quantity)
        )
        self._state.state.vice_offerings.append(offering)
        self._state.save()
        return offering

    def update_offering(
        self, offering_id: str, name: str, description: str, price: int, quantity: int
    ) -> ViceOffering:
        updated = self._validated(
            ViceOffering(offering_id, name, description, price, quantity)
        )
        index = self._index(offering_id)
        self._state.state.vice_offerings[index] = updated
        self._state.save()
        return updated

    def remove_offering(self, offering_id: str) -> None:
        index = self._index(offering_id)
        self._state.state.vice_offerings.pop(index)
        self._state.save()

    def claim(self, offering_id: str) -> ViceOffering:
        index = self._index(offering_id)
        offering = self._state.state.vice_offerings[index]
        if offering.quantity < 1:
            raise ViceError(f"{offering.name} is sold out.")
        if self.points < offering.price:
            raise ViceError(
                f"You need {offering.price - self.points} more vice points."
            )
        claimed = ViceOffering(
            offering.id, offering.name, offering.description,
            offering.price, offering.quantity - 1,
        )
        self._state.state.vice_points -= offering.price
        self._state.state.vice_offerings[index] = claimed
        self._state.save()
        return claimed

    def _index(self, offering_id: str) -> int:
        for index, offering in enumerate(self._state.state.vice_offerings):
            if offering.id == offering_id:
                return index
        raise ViceError("That vice offering no longer exists.")

    @staticmethod
    def _validated(offering: ViceOffering) -> ViceOffering:
        name = offering.name.strip()
        description = offering.description.strip()
        if not name:
            raise ViceError("A vice needs a name.")
        if not isinstance(offering.price, int) or offering.price < 1:
            raise ViceError("Price must be a positive whole number.")
        if not isinstance(offering.quantity, int) or offering.quantity < 0:
            raise ViceError("Quantity must be zero or greater.")
        return ViceOffering(
            offering.id, name, description, offering.price, offering.quantity
        )
