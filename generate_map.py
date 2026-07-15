import json
import folium
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_JSON_PATH = ROOT / "서울_레포츠.json"
OUTPUT_PATH = ROOT / "map.html"


def classify_place_category(name: str, address: str = "") -> tuple[str, str]:
    text = f"{name} {address}".lower()

    if any(keyword in text for keyword in ["수영", "풋살", "배구", "농구", "배드민턴", "체육관", "체육센터", "운동장", "스포츠센터"]):
        return "스포츠/체육", "🏀"
    if any(keyword in text for keyword in ["공원", "산책", "둘레길", "숲길", "길", "하천", "한강", "강", "호수", "정원"]):
        return "산책/러닝", "🏃"
    if any(keyword in text for keyword in ["수영장", "워터", "풀", "물놀이"]):
        return "수영", "🏊"
    if any(keyword in text for keyword in ["자전거", "자전거길", "bike"]):
        return "자전거", "🚲"
    if any(keyword in text for keyword in ["캠핑", "야영", "카라반"]):
        return "캠핑", "🏕️"
    if any(keyword in text for keyword in ["테니스", "골프", "클라이밍", "볼링", "헬스", "피트니스", "사격장"]):
        return "실내운동", "💪"
    return "기타", "📍"


def generate_map():
    # Load JSON data
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items", [])
    
    if not items:
        print("No items found in JSON file")
        return

    # Create map centered on Seoul
    seoul_center = [37.5665, 126.9780]
    map_obj = folium.Map(
        location=seoul_center,
        zoom_start=11,
        tiles="OpenStreetMap"
    )
    
    # Add markers for each place
    for item in items:
        title = item.get("title", "")
        address = item.get("addr1", "")
        lat = float(item.get("mapy", 0)) if item.get("mapy") else None
        lng = float(item.get("mapx", 0)) if item.get("mapx") else None

        if not lat or not lng:
            continue

        category, emoji = classify_place_category(title, address)

        # Create popup with category and address (no title shown)
        popup_html = f"""
        <div style="font-family: Arial; font-size: 12px; text-align: center;">
            <b>{category}</b><br>
            <small>{address}</small>
        </div>
        """

        # Create emoji icon with pin-like styling
        icon_html = f'''
        <div style="
            font-size: 32px; 
            text-align: center; 
            line-height: 32px;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
        ">
            {emoji}
        </div>
        '''
        icon = folium.DivIcon(html=icon_html)
        
        folium.Marker(
            location=[lat, lng],
            icon=icon,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{emoji} {category}"
        ).add_to(map_obj)

    # Save map
    map_obj.save(str(OUTPUT_PATH))
    print(f"Map generated successfully: {OUTPUT_PATH}")
    print(f"Total places: {len(items)}")


if __name__ == "__main__":
    generate_map()
