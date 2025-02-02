# ac-next-lvl-py-challenge

With this project, I want to cover some major topics of ArjanCodes courses:
- [Next Level Python](https://www.arjancodes.com/courses/nlp/)
- [Software Designer Mindset (Complete)](https://www.arjancodes.com/courses/tsdm/)

Main modules and topics I want to cover [current status]:
- [ ] API
- [ ] Dash
- [ ] SQLAlchemy
- [ ] Alembic
- [ ] Asyncio
- [ ] FastAPI

# Project Idea

Visualize the historical data of the stock market. 
Call the API [AlphaVantage](https://www.alphavantage.co/) to get the data and visualize it with Dash.
Possibility to save this data in a local database for further analysis.

Therefore, create a search dashboard where the user can search for available data from the AlphaVantage API.
Reduce the API calls by saving the data in a local database, because of the limited API calls per day.

## First Implementation

- [x] Create API calls to AlphaVantage
  - [x] Search for available stocks
  - [x] Get historical data of a stock
- [x] Count the API calls
- [x] Create a local database with SQLAlchemy
  - [x] Search results
  - [ ] Historical data
- [x] Visualize the data with Dash
  - [x] Search dashboard
  - [ ] Historical data dashboard
  - [ ] Save historical data in the database


## Next Steps

- [ ] Implement FastAPI to access own database for better decoupling from the Dash app and enable other applications to access the data
- [ ] Implement Asyncio to speed up the API calls