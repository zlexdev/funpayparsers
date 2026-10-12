from __future__ import annotations

from funpayparsers.types.offer_form import FormFieldKind
from funpayparsers.parsers.offer_form_parser import OfferFormParser, OfferFormParsingOptions


OPTIONS = OfferFormParsingOptions(empty_raw_source=True)

# Markup and rules as captured from `lots/offerEdit` (07.10.2026), trimmed to four fields.
FORM_HTML = """
<div class="page-content"><form action="https://funpay.com/lots/offerSave" method="post">
<input type="hidden" name="csrf_token" value="X">
<div class="lot-fields live" data-fields="[{&quot;id&quot;:&quot;method&quot;,&quot;type&quot;:5,&quot;conditions&quot;:[]},{&quot;id&quot;:&quot;region&quot;,&quot;type&quot;:5,&quot;conditions&quot;:[{&quot;id&quot;:&quot;method&quot;,&quot;list&quot;:[&quot;подарком&quot;,&quot;с заходом на аккаунт&quot;]}]},{&quot;id&quot;:&quot;region2&quot;,&quot;type&quot;:5,&quot;conditions&quot;:[{&quot;id&quot;:&quot;method&quot;,&quot;list&quot;:[&quot;цифровой ключ&quot;]}]},{&quot;id&quot;:&quot;name&quot;,&quot;type&quot;:2,&quot;conditions&quot;:[]}]">
<div class="form-group lot-field" data-id="method"><label class="control-label">Способ получения</label>
<select class="form-control lot-field-input" name="fields[method]">
<option value="">&nbsp;</option><option value="Цифровой ключ" selected>Цифровой ключ</option><option value="С заходом на аккаунт">С заходом на аккаунт</option></select></div>
<div class="form-group lot-field hidden" data-id="region"><label class="control-label">Регион</label>
<select class="form-control lot-field-input" name="fields[region]"><option value="">&nbsp;</option><option value="Россия">Россия</option></select></div>
<div class="form-group lot-field" data-id="region2"><label class="control-label">Регион</label>
<select class="form-control lot-field-input" name="fields[region2]"><option value="">&nbsp;</option><option value="Russia">Россия</option><option value="Global" selected>Global</option></select>
<p class="help-block">Где активируется ключ</p></div>
<div class="form-group lot-field" data-locale="ru" data-id="name"><label class="control-label">Название игры</label>
<input type="text" class="form-control lot-field-input" name="fields[name][ru]" value="STREET FIGHTER 6"></div>
<div class="form-group lot-field hidden" data-locale="en" data-id="name"><label class="control-label">Game title</label>
<input type="text" class="form-control lot-field-input" name="fields[name][en]" value=""></div>
</div></form></div>
"""


def _spec():
    return OfferFormParser(FORM_HTML, options=OPTIONS).parse()


def test_the_post_key_and_the_option_value_are_kept_apart_from_the_label():
    fields = {f.name: f for f in _spec().fields}
    region2 = fields['fields[region2]']
    assert region2.id == 'region2'
    assert region2.kind is FormFieldKind.SELECT
    assert [(o.value, o.label) for o in region2.options][1:] == [('Russia', 'Россия'), ('Global', 'Global')]
    assert region2.value == 'Global'
    assert region2.hint == 'Где активируется ключ'


def test_hidden_locale_twins_and_conditions_come_from_the_page():
    fields = {f.name: f for f in _spec().fields}
    assert fields['fields[region]'].hidden is True
    assert fields['fields[name][en]'].hidden is True
    assert fields['fields[name][en]'].locale == 'en'
    cond = fields['fields[region]'].conditions[0]
    assert (cond.field_id, cond.values) == ('method', ('подарком', 'с заходом на аккаунт'))
    assert fields['fields[method]'].conditions == ()


def test_shown_follows_the_controlling_field():
    spec = _spec()
    key = {f.id for f in spec.shown({'method': 'Цифровой ключ'})}
    gift = {f.id for f in spec.shown({'method': 'Подарком'})}
    assert key == {'method', 'region2', 'name'}
    assert gift == {'method', 'region', 'name'}


def test_a_page_without_rules_still_lists_the_fields():
    html = FORM_HTML.replace('data-fields=', 'data-gone=')
    fields = OfferFormParser(html, options=OPTIONS).parse().fields
    assert len(fields) == 5 and all(f.conditions == () for f in fields)
