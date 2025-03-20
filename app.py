from flask import Flask, request, jsonify
from flask_cors import CORS
import random

app = Flask(__name__)
CORS(app)

class Card:
    def __init__(self, suit, value):
        self.suit = suit
        self.value = value
        # Add rank for sorting
        self.rank = self.get_rank()

    def __str__(self):
        return f"{self.value} of {self.suit}"

    def get_rank(self):
        # Convert face cards to numeric values for sorting
        rank_map = {'J': 11, 'Q': 12, 'K': 13, 'A': 14}
        if self.value in rank_map:
            return rank_map[self.value]
        return int(self.value)

    def __lt__(self, other):
        return self.rank < other.rank

class GoFishGame:
    def __init__(self):
        self.deck = []
        self.players = [[], []]  # Player 0 (human) and Player 1 (AI)
        self.current_player = 0
        self.suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        self.values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        self.books = [0, 0]  # Track books for each player
        self.initialize_deck()
        self.deal_cards()

    def initialize_deck(self):
        self.deck = [Card(suit, value) for suit in self.suits for value in self.values]
        random.shuffle(self.deck)

    def deal_cards(self):
        # Deal 5 cards to each player
        for _ in range(5):
            for player in self.players:
                if self.deck:
                    player.append(self.deck.pop())
        # Sort initial hands
        self.players[0].sort()
        self.players[1].sort()

    def check_for_sets(self, player_index):
        player_hand = self.players[player_index]
        sets = []
        values_count = {}
        
        for card in player_hand:
            values_count[card.value] = values_count.get(card.value, 0) + 1
        
        for value, count in values_count.items():
            if count == 4:
                sets.append(value)
                # Remove the set from player's hand
                self.players[player_index] = [card for card in player_hand if card.value != value]
                # Increment books count
                self.books[player_index] += 1
        
        return sets

    def ask_for_cards(self, from_player, to_player, value):
        matching_cards = [card for card in self.players[to_player] if card.value == value]
        
        if matching_cards:
            # Transfer matching cards
            self.players[from_player].extend(matching_cards)
            self.players[to_player] = [card for card in self.players[to_player] if card.value != value]
            # Sort the receiving player's hand
            self.players[from_player].sort()
            return True, matching_cards
        else:
            # Go fish
            if self.deck:
                new_card = self.deck.pop()
                self.players[from_player].append(new_card)
                # Sort the player's hand after adding new card
                self.players[from_player].sort()
            return False, []

    def is_game_over(self):
        return len(self.deck) == 0 and (len(self.players[0]) == 0 or len(self.players[1]) == 0)

    def get_winner(self):
        if len(self.players[0]) == 0:
            return 0
        elif len(self.players[1]) == 0:
            return 1
        return None

    def ai_make_move(self):
        # Simple AI strategy: ask for a card value that appears most frequently in AI's hand
        if not self.players[1]:
            return False, [], []

        # Count values in AI's hand
        values_count = {}
        for card in self.players[1]:
            values_count[card.value] = values_count.get(card.value, 0) + 1

        # Find the most frequent value
        most_frequent_value = max(values_count.items(), key=lambda x: x[1])[0]

        # Ask for cards from the human player
        success, cards = self.ask_for_cards(1, 0, most_frequent_value)
        
        # Check for sets after the move
        sets = self.check_for_sets(1)
        
        # If no cards were received and deck is empty, end turn
        if not success and not self.deck:
            self.current_player = 0
            return False, [], sets
        
        # If no cards were received but deck has cards, draw one
        if not success and self.deck:
            new_card = self.deck.pop()
            self.players[1].append(new_card)
            self.players[1].sort()
            self.current_player = 0
            return False, [new_card], sets

        return success, cards, sets

# Global game instance
game = None

def get_game_state():
    if game is None:
        return jsonify({
            'error': 'No active game. Please start a new game.',
            'game_over': True
        }), 400
    return None

@app.route('/api/new-game', methods=['POST'])
def new_game():
    global game
    game = GoFishGame()
    return jsonify({
        'player1_hand': [str(card) for card in game.players[0]],
        'player2_hand': [str(card) for card in game.players[1]],
        'current_player': game.current_player,
        'books': game.books
    })

@app.route('/api/ask-cards', methods=['POST'])
def ask_cards():
    error_response = get_game_state()
    if error_response:
        return error_response

    data = request.json
    from_player = data.get('from_player')
    to_player = data.get('to_player')
    value = data.get('value')

    if from_player != game.current_player:
        return jsonify({
            'error': 'Not your turn',
            'current_player': game.current_player
        }), 400

    success, cards = game.ask_for_cards(from_player, to_player, value)
    
    # Check for sets after the move
    sets = game.check_for_sets(from_player)
    
    # Switch turns if the move wasn't successful
    if not success:
        game.current_player = 1 - game.current_player

    return jsonify({
        'success': success,
        'cards': [str(card) for card in cards],
        'sets': sets,
        'player1_hand': [str(card) for card in game.players[0]],
        'player2_hand': [str(card) for card in game.players[1]],
        'current_player': game.current_player,
        'game_over': game.is_game_over(),
        'winner': game.get_winner(),
        'books': game.books
    })

@app.route('/api/ai-move', methods=['POST'])
def ai_move():
    error_response = get_game_state()
    if error_response:
        return error_response

    if game.current_player != 1:
        return jsonify({
            'error': 'Not AI\'s turn',
            'current_player': game.current_player
        }), 400

    success, cards, sets = game.ai_make_move()

    return jsonify({
        'success': success,
        'cards': [str(card) for card in cards],
        'sets': sets,
        'player1_hand': [str(card) for card in game.players[0]],
        'player2_hand': [str(card) for card in game.players[1]],
        'current_player': game.current_player,
        'game_over': game.is_game_over(),
        'winner': game.get_winner(),
        'books': game.books
    })

if __name__ == '__main__':
    app.run(debug=True) 