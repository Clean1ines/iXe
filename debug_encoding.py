import logging
import re
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def analyze_encoding(text):
    """Analyze if text has double encoding issues"""
    logger.info(f"=== Analyzing text: '{text[:50]}...' ===")
    
    # Check for double-encoded Cyrillic patterns
    patterns = [
        r'[РЎРљРРРРРРЁРРРРРЎРРСРСР].*[РЎРљРРРРРРЁРРРРРЎРРСРСР]',
        r'[РС][^\x00-\x7F]',
        r'РљРРЎ',
        r'РљРћРЎ'
    ]
    
    for pattern in patterns:
        if re.search(pattern, text):
            logger.info(f"✓ Found double-encoding pattern: '{pattern}'")
    
    # Count 'Р' and 'С' characters
    r_count = text.count('Р')
    s_count = text.count('С')
    total_len = len(text)
    
    if total_len > 0:
        r_ratio = r_count / total_len
        s_ratio = s_count / total_len
        logger.info(f"'Р' count: {r_count} ({r_ratio:.2%}), 'С' count: {s_count} ({s_ratio:.2%})")
    
    # Try to fix encoding
    try:
        fixed_text = text.encode('windows-1251').decode('utf-8', errors='replace')
        logger.info(f"Fixed text: '{fixed_text[:50]}...'")
        
        # Check if fixed text has Cyrillic characters
        has_cyrillic = bool(re.search(r'[а-яА-ЯёЁ]', fixed_text))
        logger.info(f"Fixed text has Cyrillic: {has_cyrillic}")
        
        return fixed_text
    except (UnicodeEncodeError, UnicodeDecodeError) as e:
        logger.error(f"Encoding fix failed: {e}")
        return text

if __name__ == "__main__":
    # Example from Knowledge Base
    kb_text = "РљРРЎ: 4.1 РџСЂРѕРёР·РІРѕРґРЅР°СЏ С„СѓРЅРєС†РёРё. РџСЂРѕРёР·РІРѕРґРЅС‹Рµ СЌР»РµРјРµРЅС‚Р°СЂРЅС‹С… С„СѓРЅРєС†РёР№ 4.2 РџСЂРёРјРµРЅРµРЅРёРµ РїСЂРѕРёР·РІРѕРґРЅРѕР№ Рє РёСЃСЃР»РµРґРѕРІР°РЅРёСЋ С„СѓРЅРєС†РёР№ РЅР° РјРѕРЅРѕС‚РѕРЅРЅРѕСЃС‚СЊ Рё СЌРєСЃС‚СЂРµРјСѓРјС‹"
    
    # Example from logs (double-encoded)
    log_text = "iСВОЙСТВА ЗАДАНИЯКЭС:7.5 Коорд..."
    
    analyze_encoding(kb_text)
    print("\n")
    analyze_encoding(log_text)
