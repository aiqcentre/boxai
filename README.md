# 🎬 Film Analytics & Prediction ChatBot

This application combines film data analytics, Australian location information, and box office prediction capabilities.

---

## 🔗 API ENDPOINTS

### 🇦🇺 Australian State & City Information

<!-- AU_DATA_START -->
https://au-state-city-information-api.onrender.com/au/states
https://au-state-city-information-api.onrender.com/au/capital?state=STATE_OR_TERRITORY
https://au-state-city-information-api.onrender.com/au/cities?state=STATE_OR_TERRITORY
https://au-state-city-information-api.onrender.com/au/state-of-city?city=CITY
<!-- AU_DATA_END -->

#### Description

| Endpoint | Description | Example |
|-----------|--------------|----------|
| `/au/states` | List all Australian states and territories | — |
| `/au/capital` | Get the capital city of a state or territory | `/au/capital?state=Queensland` → Brisbane |
| `/au/cities` | Get major cities in a specific state | `/au/cities?state=Victoria` → Melbourne, Geelong… |
| `/au/state-of-city` | Get which state a city belongs to | `/au/state-of-city?city=Hobart` → Tasmania |

---

### 🎯 Box Office Prediction API

<!-- PREDICT_DATA_START -->
https://films-predict-app-wex9u.ondigitalocean.app/
https://films-predict-app-wex9u.ondigitalocean.app/predict1
https://films-predict-app-wex9u.ondigitalocean.app/predict2
<!-- PREDICT_DATA_END -->

#### Description

| Endpoint | Method | Description | Request Body |
|----------|--------|-------------|--------------|
| `/predict1` | POST | Predict first week box office gross | `{"censorRating": "PG", "distributorName": "Disney", "week_date": "2024-01-15", "concurrent_films": []}` |
| `/predict2` | POST | Predict final total gross from week 1 | `{"wk1_total": 5000000.0}` |

#### Request Examples

**Predict Week 1 Gross (`/predict1`)**
```json
{
  "censorRating": "M",
  "distributorName": "Universal Pictures",
  "week_date": "2024-03-20",
  "concurrent_films": []
}
```

**Response:**
```json
{
  "predicted_gross": 4523891.50
}
```

**Predict Final Total (`/predict2`)**
```json
{
  "wk1_total": 5000000.0
}
```

**Response:**
```json
{
  "predicted_gross": 15234567.89
}
```

---

## 🧠 How It Works

The `app.py` automatically:

1. **Reads this README file**
2. **Extracts all URLs** between:
   - `<!-- AU_DATA_START -->` and `<!-- AU_DATA_END -->` for Australian data
   - `<!-- PREDICT_DATA_START -->` and `<!-- PREDICT_DATA_END -->` for prediction APIs
3. **Parses and loads them** dynamically into chatbot tools
4. **Routes queries** based on keywords:
   - **Prediction queries** → Use prediction API tools
   - **Australian queries** → Use AU location tools
   - **Film data queries** → Generate SQL and query database

---

## 💬 Example Questions

### Film Analytics (SQL-based)
- "Show me the top 5 films by weekend gross in July 2023"
- "What are the highest-grossing films from Universal Pictures?"
- "List films released between January and March 2024"

### Box Office Predictions (API-based)
- "Predict the first week gross for a film with PG rating from Disney releasing on 2024-06-15"
- "If a film makes $3 million in week 1, what will be the final total?"
- "Estimate box office for an M-rated Warner Bros film"

### Australian Location Info (API-based)
- "What is the capital of Queensland?"
- "List all Australian states"
- "Which state is Melbourne in?"
- "What cities are in New South Wales?"

---

## 🛠️ Technical Features

### Multi-Agent Architecture
- **SQL Agent**: Generates safe, read-only DuckDB queries
- **AU Agent**: Handles Australian location queries via REST API
- **Predict Agent**: Manages box office predictions with database integration
- **Answer Agent**: Synthesizes natural language responses

### Safety Features
- Read-only database access
- SQL injection prevention
- Destructive query blocking
- Input validation and sanitization

### Prediction Intelligence
The chatbot can:
1. **Query the database** for film details (rating, distributor, release date)
2. **Call prediction APIs** with retrieved data
3. **Combine predictions** (week 1 → final total)
4. **Format results** as currency with context

---

## 📦 Dependencies

- `streamlit` - Web interface
- `duckdb` - Database queries
- `pydantic-ai` - AI agent framework
- `httpx` - HTTP client for API calls
- `pandas` - Data manipulation
- `logfire` - Observability

---

## 🚀 Usage

```bash
# Set environment variables
export OPENAI_API_KEY="your-key-here"

# Run the application
streamlit run app.py
```

The app will automatically discover and integrate all APIs defined in this README.

---

## 🔄 Adding New Endpoints

To add new endpoints, simply update the appropriate section:

```text
<!-- PREDICT_DATA_START -->
https://films-predict-app-wex9u.ondigitalocean.app/predict3
<!-- PREDICT_DATA_END -->
```

The app will automatically detect and integrate new endpoints on restart.