"""Conservative listing templates built only from explicit source text."""
import json
from pathlib import Path
import re

ROOT_DIR = Path(__file__).resolve().parents[3]
FEES_FILE = ROOT_DIR / 'rules' / 'real_estate_fees.json'
AREAS_FILE = ROOT_DIR / 'knowledge' / 'real_estate_areas.json'

def load_fees_rules():
    if FEES_FILE.exists():
        try:
            return json.loads(FEES_FILE.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {}

def load_market_areas():
    if AREAS_FILE.exists():
        try:
            return json.loads(AREAS_FILE.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {}

def calculate_fees(price_aed, emirate='ajman', is_gcc=True, is_rental=False):
    """Deterministic fee calculation for Ajman and Sharjah real estate transactions."""
    fees_data = load_fees_rules()
    emirate_key = 'sharjah' if 'sharjah' in str(emirate).lower() or 'الشارقة' in str(emirate) else 'ajman'
    rules = fees_data.get(emirate_key, {})
    price_val = float(price_aed)
    
    if is_rental:
        rate = rules.get('tenancy_attestation_rate', 0.02)
        attestation = price_val * rate
        commission = price_val * rules.get('brokerage_commission_rate', 0.02)
        return {
            'emirate': emirate_key,
            'annual_rent': price_val,
            'attestation_fee': attestation,
            'commission': commission,
            'total_initial_costs': attestation + commission,
            'notes': rules.get('notes', '')
        }
    
    rate_map = rules.get('transfer_fee_rate', {'citizen_gcc': 0.02, 'foreign_expat': 0.02})
    transfer_rate = rate_map.get('citizen_gcc' if is_gcc else 'foreign_expat', 0.02)
    transfer_fee = price_val * transfer_rate
    commission = price_val * rules.get('brokerage_commission_rate', 0.02)
    title_deed = rules.get('title_deed_fee', 1000)
    
    return {
        'emirate': emirate_key,
        'purchase_price': price_val,
        'transfer_fee': transfer_fee,
        'commission': commission,
        'title_deed_fee': title_deed,
        'total_closing_costs': transfer_fee + commission + title_deed,
        'notes': rules.get('notes', '')
    }

_TYPE_TERMS = (
    (('شقة', 'apartment', 'flat'), 'شقة', 'apartment'),
    (('فيلا', 'villa'), 'فيلا', 'villa'),
    (('أرض', 'اراض', 'land', 'plot'), 'أرض', 'land'),
    (('استوديو', 'studio'), 'استوديو', 'studio'),
    (('مكتب', 'office'), 'مكتب', 'office'),
)
_PRICE = re.compile(
    r'(?:AED|د\.?\s*إ|درهم(?:\s+إماراتي)?)\s*[\d,]+(?:\.\d+)?|'
    r'[\d,]+(?:\.\d+)?\s*(?:AED|د\.?\s*إ|درهم(?:\s+إماراتي)?)',
    re.IGNORECASE,
)
_AREA = re.compile(
    r'[\d,]+(?:\.\d+)?\s*(?:sq\.?\s*ft|sqft|sqm|متر(?:\s+مربع)?|قدم(?:\s+مربع)?)',
    re.IGNORECASE,
)
_UNKNOWN_PRICE = re.compile(r'(?:السعر|price).{0,20}(?:غير معروف|غير محدد|مجهول|unknown|not known)',re.I)
_UNKNOWN_AREA = re.compile(r'(?:المساحة|area).{0,20}(?:غير معروفة|غير محددة|مجهولة|unknown|not known)',re.I)


def is_listing_request(text):
    return isinstance(text,str) and bool(re.search(
        r'إعلان|اعلان|مسودة\s+إعلان|listing\s+draft|listing\s+copy|ad\s+copy',
        text,
        re.IGNORECASE,
    ))


def _property_type(text,arabic):
    label_index=1 if arabic else 2
    return next((item[label_index] for item in _TYPE_TERMS
                 if any(re.search(re.escape(term),text,re.IGNORECASE) for term in item[0])),None)


def build_listing_draft(text):
    if not isinstance(text,str) or not text.strip():
        raise ValueError('بيانات الإعلان غير صالحة.')
    arabic=bool(re.search(r'[\u0600-\u06ff]',text))
    property_type=_property_type(text,arabic)
    normalized=text.casefold()
    if 'للإيجار' in text or 'للايجار' in text or 'إيجار' in text or 'تأجير' in text or re.search(r'\b(?:rent|rental|lease)\b',normalized):
        transaction='للإيجار' if re.search(r'[\u0600-\u06ff]',text) else 'for rent'
    elif 'للبيع' in text or 'بيع' in text or re.search(r'\b(?:sale|for sale)\b',normalized):
        transaction='للبيع' if re.search(r'[\u0600-\u06ff]',text) else 'for sale'
    else:
        transaction='[نوع العرض غير محدد]'
    emirate=next((city for terms,city in (
        (('عجمان','ajman'),'عجمان'),
        (('الشارقة','شارقة','sharjah'),'الشارقة'),
    ) if any(re.search(re.escape(term),text,re.IGNORECASE) for term in terms)),None)
    if not arabic:
        emirate=next((city for terms,city in (
            (('ajman',),'Ajman'),
            (('sharjah',),'Sharjah'),
        ) if any(re.search(re.escape(term),text,re.IGNORECASE) for term in terms)),None)

    price=None if _UNKNOWN_PRICE.search(text) else _PRICE.search(text)
    area=None if _UNKNOWN_AREA.search(text) else _AREA.search(text)
    title=' '.join(value for value in (property_type or ('عقار' if emirate or re.search(r'[\u0600-\u06ff]',text) else 'Property'),transaction,emirate) if value)
    if re.search(r'[\u0600-\u06ff]',text):
        return '\n'.join((
            'مسودة إعلان — غير جاهزة للنشر قبل مراجعة البيانات',
            f'العنوان: {title}',
            f'السعر: {price.group(0) if price else "[يُضاف بعد التأكيد]"}',
            f'المساحة: {area.group(0) if area else "[تُضاف بعد التأكيد]"}',
            f'الموقع التفصيلي: {emirate or "[يُحدد]"} — [المنطقة/المبنى غير مذكور]',
            'التوافر: [يحتاج تأكيدًا من المالك]',
            'المزايا والمواصفات: [أضف المعلومات المؤكدة فقط]',
            'قبل النشر: راجع السعر والمساحة والموقع والتوافر والحقوق.',
        ))
    return '\n'.join((
        'Listing draft — verify before publishing',
        f'Title: {title}',
        f'Price: {price.group(0) if price else "[add after confirmation]"}',
        f'Area: {area.group(0) if area else "[add after confirmation]"}',
        f'Exact location: {emirate or "[not provided]"} — [area/building not provided]',
        'Availability: [confirm with the owner]',
        'Features: [add verified details only]',
        'Before publishing: verify price, area, location, availability, and usage rights.',
    ))
