import logging
from bs4 import BeautifulSoup
from infrastructure.adapters.html_metadata_extractor_adapter import HTMLMetadataExtractorAdapter

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_with_real_examples():
    adapter = HTMLMetadataExtractorAdapter()
    
    # Example 1: From logs - header with id='i40B442'
    example1_html = '''
    <div id="i40B442" class="qhead">
        <span class="canselect">40B442</span>
        iСВОЙСТВА ЗАДАНИЯ
        <br/>
        КЭС:7.5 Координаты и векторы
    </div>
    '''
    soup1 = BeautifulSoup(example1_html, 'html.parser')
    header1 = soup1.find('div')
    # Add custom attributes to simulate parser behavior
    header1.attrs['extracted_id'] = '40B442'
    
    print("=== Example 1: From logs ===")
    result1 = adapter.extract(header1)
    print(f"Task ID: {result1['task_id']}")
    print(f"Task number: {result1['task_number']}")
    print(f"KES codes: {result1['kes_codes']}")
    print(f"KOS codes: {result1['kos_codes']}")
    
    # Example 2: From Knowledge Base - double-encoded text
    example2_html = '''
    <tr>
        <td>РљРРЎ:</td>
        <td>4.1 РџСЂРѕРёР·РІРѕРґРЅР°СЏ С„СѓРЅРєС†РёРё. РџСЂРѕРёР·РІРѕРґРЅС‹Рµ СЌР»РµРјРµРЅС‚Р°СЂРЅС‹С… С„СѓРЅРєС†РёР№ 4.2 РџСЂРёРјРµРЅРµРЅРёРµ РїСЂРѕРёР·РІРѕРґРЅРѕР№ Рє РёСЃСЃР»РµРґРѕРІР°РЅРёСЋ С„СѓРЅРєС†РёР№ РЅР° РјРѕРЅРѕС‚РѕРЅРЅРѕСЃС‚СЊ Рё СЌРєСЃС‚СЂРµРјСѓРјС‹. РќР°С…РѕР¶РґРµРЅРёРµ РЅР°РёР±РѕР»СЊС€РµРіРѕ Рё РЅР°РёРјРµРЅСЊС€РµРіРѕ Р·РЅР°С‡РµРЅРёСЏ С„СѓРЅРєС†РёРё РЅР° РѕС‚СЂРµР·РєРµ</td>
    </tr>
    '''
    soup2 = BeautifulSoup(example2_html, 'html.parser')
    header2 = soup2.find('tr')
    
    print("\n=== Example 2: From Knowledge Base (double-encoded) ===")
    result2 = adapter.extract(header2)
    print(f"Task number: {result2['task_number']}")
    print(f"KES codes: {result2['kes_codes']}")
    print(f"KOS codes: {result2['kos_codes']}")

    # Example 3: Real example from the debug logs with double encoding
    example3_html = '''
    <div id="i4CBD4E" class="qhead">
        <span class="canselect">4CBD4E</span>
        iСВОЙСТВА ЗАДАНИЯ
        <br/>
        РљРРЎ:2.1 Целые числа
    </div>
    '''
    soup3 = BeautifulSoup(example3_html, 'html.parser')
    header3 = soup3.find('div')
    header3.attrs['extracted_id'] = '4CBD4E'
    
    print("\n=== Example 3: Real example from debug logs (double-encoded text) ===")
    result3 = adapter.extract(header3)
    print(f"Task ID: {result3['task_id']}")
    print(f"Task number: {result3['task_number']}")
    print(f"KES codes: {result3['kes_codes']}")
    print(f"KOS codes: {result3['kos_codes']}")

if __name__ == "__main__":
    test_with_real_examples()
