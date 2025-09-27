from pathlib import Path
import re
import json
from typing import List, Dict, Optional
MARKER_START = "AU_DATA_START"
MARKER_END = "AU_DATA_END"
def read_file(filename:str ="README.md") -> Dict:
    """
    Args:
      filename: name of the file to read
    Return: dictionary of the data
    """
    text = Path(filename).read_text(encoding="utf-8")
    m = re.search(
        rf"<!--\s*{MARKER_START}\s*-->(.*?)<!--\s*{MARKER_END}\s*-->",
        text, flags=re.DOTALL | re.IGNORECASE
    )
    if not m:
        raise ValueError("AU data markers not found in README.md")
    block = m.group(1)
    j = re.search(r"```json(.*?)```", block, flags=re.DOTALL | re.IGNORECASE)
    if not j:
        raise ValueError("JSON block not found between markers")
    return json.loads(j.group(1))
def index():
    data = read_file()
    states = data.get("states_and_territories", [])
    by_state = {s["name"].lower(): s for s in states}
    city_to_state = {}
    for s in states:
        capital = s.get("capital")
        majors = s.get("major_cities",[]) or []
        for c in [capital, *majors]:
           if not c:
               continue
           city_to_state.setdefault(c.lower(), set()).add(s["name"])
    return states, by_state, city_to_state
def norm(s:str) ->str:
    return s.strip().lower()

### Tools ###
def au_list_states() -> List[str]:
    states, *_ = index()
    return [s["name"] for s in states]
def au_capital_of(state_or_territory: str) -> Optional[str]:
    _, by_state, _ = index()
    s = by_state.get(norm(state_or_territory))
    return s.get("capital") if s else None
def au_cities_in(state_or_territory:str) -> Optional[List[str]]:
    _, by_state, _ = index()
    s = by_state.get(norm(state_or_territory))
    if not s: 
        return None
    majors = s.get("major_cities",[]) or []
    out = set([s.get("capital","")] + majors)
    return sorted([c for c in out if c])
def au_state_of_city(city:str) -> List[str]:
    _, _, city_to_state = index()
    return sorted(city_to_state.get(norm(city),[]))

if __name__ == "__main__":
    print(au_state_of_city("Sydney"))
