from __future__ import annotations


__all__ = ('OfferFormParser', 'OfferFormParsingOptions')

import json
from typing import Any
from dataclasses import dataclass

from selectolax.lexbor import LexborNode

from funpayparsers.parsers.base import ParsingOptions, FunPayHTMLObjectParser
from funpayparsers.types.offer_form import (
    FormField,
    FormOption,
    FormFieldKind,
    OfferFormSpec,
    FormCondition,
)


@dataclass(frozen=True)
class OfferFormParsingOptions(ParsingOptions):
    """Options class for ``OfferFormParser``."""

    ...


_KINDS = {'select': FormFieldKind.SELECT, 'textarea': FormFieldKind.TEXTAREA}
_INPUT_KINDS = {
    'text': FormFieldKind.TEXT,
    'checkbox': FormFieldKind.CHECKBOX,
    'hidden': FormFieldKind.HIDDEN,
}


class OfferFormParser(FunPayHTMLObjectParser[OfferFormSpec, OfferFormParsingOptions]):
    """
    Parses the category fields of a lot form: ids, labels, options, show rules.

    The show rules live in the form itself: ``div.lot-fields[data-fields]`` is a JSON list of
    ``{id, type, conditions: [{id, list}]}`` (capture of ``lots/offerEdit``, 07.10.2026).
    ``OfferFieldsParser`` stays the parser of the values a save posts; this one describes what
    may be posted.

    Possible locations:
        - Offer creating page (`https://funpay.com/lots/offerEdit?node=<node_id>`)
        - Offer editing page
        (`https://funpay.com/lots/offerEdit?node=<node_id>&offer=<offer_id>`)
    """

    def _parse(self) -> OfferFormSpec:
        rules = self._rules()
        fields: list[FormField] = []
        for group in self.tree.css('div.lot-field'):
            parsed = self._field(group, rules)
            if parsed is not None:
                fields.append(parsed)
        return OfferFormSpec(raw_source=self.tree.html or '', fields=fields)

    def _rules(self) -> dict[str, dict[str, Any]]:
        holder = self.tree.css_first('[data-fields]', strict=False, default=None)
        if holder is None:
            return {}
        try:
            rows = json.loads(holder.attributes.get('data-fields') or '[]')
        except ValueError:
            return {}
        return {str(row.get('id')): row for row in rows if isinstance(row, dict)}

    def _field(self, group: LexborNode, rules: dict[str, dict[str, Any]]) -> FormField | None:
        control = group.css_first(
            'select.lot-field-input, textarea.lot-field-input, input.lot-field-input',
            strict=False,
            default=None,
        )
        if control is None:
            return None
        field_id = group.attributes.get('data-id') or ''
        rule = rules.get(field_id, {})
        label = group.css_first('label.control-label', strict=False, default=None)
        hint = group.css_first('p.help-block', strict=False, default=None)
        options = tuple(self._choices(control)) if control.tag == 'select' else ()
        selected = next((o.value for o in options if o.selected), '')
        return FormField(
            id=field_id,
            name=control.attributes.get('name') or '',
            label=label.text(strip=True) if label is not None else '',
            kind=self._kind(control),
            locale=group.attributes.get('data-locale'),
            value=selected if control.tag == 'select' else self._value(control),
            options=options,
            hint=hint.text(strip=True) if hint is not None else '',
            hidden='hidden' in (group.attributes.get('class') or '').split(),
            type_code=rule.get('type') if isinstance(rule.get('type'), int) else None,
            conditions=tuple(
                FormCondition(
                    field_id=str(cond.get('id')),
                    values=tuple(str(v).lower() for v in cond.get('list') or ()),
                )
                for cond in rule.get('conditions') or ()
                if isinstance(cond, dict)
            ),
        )

    @staticmethod
    def _kind(control: LexborNode) -> FormFieldKind:
        if control.tag in _KINDS:
            return _KINDS[control.tag]
        kind = (control.attributes.get('type') or 'text').lower()
        return _INPUT_KINDS.get(kind, FormFieldKind.OTHER)

    @staticmethod
    def _value(control: LexborNode) -> str:
        if control.tag == 'textarea':
            return control.text() or ''
        return control.attributes.get('value') or ''

    @staticmethod
    def _choices(select: LexborNode) -> list[FormOption]:
        return [
            FormOption(
                value=option.attributes.get('value') or '',
                label=(option.text() or '').replace('\xa0', ' ').strip(),
                selected='selected' in option.attributes,
            )
            for option in select.css('option')
        ]
