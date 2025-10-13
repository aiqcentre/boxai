# 🇦🇺 AU State & City Information API — Endpoints

This section defines all public endpoints that provide Australian city and state data.
The app automatically reads this section to discover available APIs.

---

## 🔗 API ENDPOINTS
<!-- AU_DATA_START -->
https://au-state-city-information-api.onrender.com/au/states
https://au-state-city-information-api.onrender.com/au/capital?state=STATE_OR_TERRITORY
https://au-state-city-information-api.onrender.com/au/cities?state=STATE_OR_TERRITORY
https://au-state-city-information-api.onrender.com/au/state-of-city?city=CITY
<!-- AU_DATA_END -->

---

### 🧩 Description

| Endpoint | Description | Example |
|-----------|--------------|----------|
| `/au/states` | List all Australian states and territories | — |
| `/au/capital` | Get the capital city of a state or territory | `/au/capital?state=Queensland` → Brisbane |
| `/au/cities` | Get major cities in a specific state | `/au/cities?state=Victoria` → Melbourne, Geelong… |
| `/au/state-of-city` | Get which state a city belongs to | `/au/state-of-city?city=Hobart` → Tasmania |

---

### 🧠 Integration

The `app.py` automatically:
1. Reads this README file.
2. Extracts all URLs between `<!-- AU_DATA_START -->` and `<!-- AU_DATA_END -->`.
3. Parses them using regex.
4. Dynamically loads them into the chatbot tools.

You can safely update or add new endpoints here, e.g.:

```text
https://au-state-city-information-api.onrender.com/au/population?state=Queensland
