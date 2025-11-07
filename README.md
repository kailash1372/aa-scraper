# American Airlines Award vs Cash Price Comparison

This Python project compares **award flight prices** and **cash prices** for American Airlines routes by querying the airline’s booking API. It automates cookie retrieval with **Playwright**, uses **curl_cffi** for HTTP requests, and outputs a clean JSON file summarizing flight options and cents-per-point (CPP) values.

---

## ✈️ Features

- Fetches **live pricing data** (cash + award) from [aa.com](https://www.aa.com)
- Uses **Playwright** to obtain valid session cookies
- Asynchronous API calls with **curl_cffi.AsyncSession**
- Automatically calculates **cents-per-point (CPP)** for each flight
- Saves structured output as `result.json`

---

## 🧰 Tech Stack

- Python 3.10+
- [Playwright](https://playwright.dev/python/)
- [curl_cffi](https://github.com/yifeikong/curl_cffi)
- Docker (optional, for containerized usage)

---

## 📦 Installation

### 🖥️ Option 1: Run Locally

1. **Clone this repository**
   ```bash
   git clone https://github.com/kailash1372/aa-scraper.git
   cd aa-scraper
``

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   playwright install
   ```

3. **Run the script**

   ```bash
   python aa_scraper.py
   ```

   The script will launch a Playwright-controlled Chromium browser to fetch cookies automatically.

4. **Check the output**
   After successful execution, a file named `result.json` will be created in the same directory.

---

## 📁 Output Example

```json
{
  "search_metadata": {
    "origin": "LAX",
    "destination": "JFK",
    "date": "2025-12-15",
    "passengers": 1,
    "cabin_class": "economy"
  },
  "flights": [
    {
      "is_nonstop": true,
      "segments": [
        {
          "flight_number": "AA100",
          "departure_time": "08:00",
          "arrival_time": "16:15"
        }
      ],
      "total_duration": "8h 15m",
      "points_required": 18000,
      "cash_price_usd": 220.5,
      "taxes_fees_usd": 5.6,
      "cpp": 1.2
    }
  ],
  "total_results": 1
}
```

---


## ⚠️ Disclaimer

This project is for **educational and research purposes only**.
Do **not** use it for commercial purposes or high-frequency scraping.
Always respect the target website’s terms of service and robots.txt.

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
