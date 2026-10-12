from __future__ import annotations


__all__ = ('FormCondition', 'FormFieldKind', 'FormOption', 'FormField', 'OfferFormSpec')

from enum import Enum
from dataclasses import field, dataclass

from funpayparsers.types.base import FunPayObject


class FormFieldKind(str, Enum):
    """Widget of a lot form field, taken from the control's HTML tag, not from FunPay's type codes."""

    TEXT = 'text'
    TEXTAREA = 'textarea'
    SELECT = 'select'
    CHECKBOX = 'checkbox'
    HIDDEN = 'hidden'
    OTHER = 'other'


@dataclass
class FormOption:
    """One choice of a select field."""

    value: str
    """What the form posts. Differs from ``label`` (``Russia`` vs ``Россия``)."""

    label: str
    """What the seller reads."""

    selected: bool = False


@dataclass
class FormCondition:
    """A field is shown only while ANOTHER field holds one of these values."""

    field_id: str
    """``data-id`` of the controlling field."""

    values: tuple[str, ...]
    """Lower-cased values, as FunPay's own script compares them."""


@dataclass
class FormField:
    """One category field of a lot form (``div.lot-field[data-id]``)."""

    id: str
    """``data-id``: the field's identity, shared by its locale twins (``name`` ru and en)."""

    name: str
    """The ``name`` attribute: the key a save posts (``fields[region]``, ``fields[name][ru]``)."""

    label: str
    kind: FormFieldKind
    locale: str | None = None
    """``data-locale`` of a multilingual field; ``None`` for a plain one."""

    value: str = ''
    """Current value (the selected option's value for a select)."""

    options: tuple[FormOption, ...] = ()
    hint: str = ''
    hidden: bool = False
    """The ``hidden`` class at render time: not applicable to the current values, or a locale twin."""

    type_code: int | None = None
    """FunPay's own number from ``data-fields`` (2 text, 3 textarea, 4/5 select, 6 images)."""

    conditions: tuple[FormCondition, ...] = ()
    """All must hold for the field to be shown; empty means always."""


@dataclass
class OfferFormSpec(FunPayObject):
    """The category fields of a lot form with their ids, options and show rules."""

    fields: list[FormField] = field(default_factory=list)

    def shown(self, values: dict[str, str]) -> list[FormField]:
        """Fields the form shows when the fields of ``values`` (``id`` -> value) are set.

        A condition holds when the controlling field's value, lower-cased, is in its list;
        a controlling field absent from ``values`` counts as empty.
        """
        result: list[FormField] = []
        for item in self.fields:
            if item.locale not in (None, 'ru'):
                continue
            if all(
                values.get(cond.field_id, '').lower() in cond.values for cond in item.conditions
            ):
                result.append(item)
        return result
