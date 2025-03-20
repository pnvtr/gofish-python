# Go Fish Card Game

A web-based implementation of the classic Go Fish card game using Python (Flask) for the backend and React for the frontend.

## Setup Instructions

### Backend Setup

1. Create a Python virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install the required Python packages:
```bash
pip install -r requirements.txt
```

3. Run the Flask backend:
```bash
python app.py
```

The backend will run on http://localhost:5000

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install the required Node.js packages:
```bash
npm install
```

3. Start the React development server:
```bash
npm start
```

The frontend will run on http://localhost:3000

## How to Play

1. Open your browser and navigate to http://localhost:3000
2. Click "New Game" to start a new game
3. Each player is dealt 5 cards
4. On your turn:
   - Select a card from your hand
   - Click "Ask for Cards" to ask the other player for cards of that value
   - If the other player has matching cards, they will be transferred to your hand
   - If not, you'll "Go Fish" and draw a card from the deck
5. Collect sets of 4 cards of the same value to win
6. The game ends when a player runs out of cards or the deck is empty

## Game Rules

- Players take turns asking each other for cards
- When asking for cards, you must have at least one card of the requested value in your hand
- If the other player has the requested cards, they must give them to you
- If they don't have the cards, you must "Go Fish" and draw a card from the deck
- Collect sets of 4 cards of the same value to win
- The game ends when a player runs out of cards or the deck is empty 