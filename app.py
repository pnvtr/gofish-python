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
        # Enhanced AI memory
        self.ai_memory = {
            'asked_cards': set(),  # Cards AI has asked for
            'received_cards': set(),  # Cards AI has received from player
            'player_asked_for': set(),  # Cards player has asked for
            'player_received': set(),  # Cards player has received
            'last_asked_value': None,  # Last value AI asked for
            'consecutive_failures': 0,  # Number of consecutive failed requests
            'card_probabilities': {},  # Probability of cards being in player's hand
            'player_behavior': {},  # Track player's asking patterns
            'known_cards': set(),  # All cards that have been seen
            'last_player_ask': None,  # Last card player asked for
            'successful_asks': {},  # Track successful asks for each card value
            'failed_asks': {},  # Track failed asks for each card value
            'turn_count': 0  # Track number of turns
        }
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
        # Update AI memory before the move
        if from_player == 1:  # If AI is asking
            self.ai_memory['asked_cards'].add(value)
            self.ai_memory['last_asked_value'] = value
        else:  # If human is asking
            self.ai_memory['player_asked_for'].add(value)
            self.ai_memory['last_player_ask'] = value

        matching_cards = [card for card in self.players[to_player] if card.value == value]
        
        if matching_cards:
            # Transfer matching cards
            self.players[from_player].extend(matching_cards)
            self.players[to_player] = [card for card in self.players[to_player] if card.value != value]
            # Sort the receiving player's hand
            self.players[from_player].sort()
            
            # Update AI memory with successful ask
            if from_player == 1:
                self.ai_memory['successful_asks'][value] = self.ai_memory['successful_asks'].get(value, 0) + 1
                self.ai_memory['received_cards'].update(card.value for card in matching_cards)
            else:
                self.ai_memory['player_received'].update(card.value for card in matching_cards)
            
            return True, matching_cards
        else:
            # Go fish
            if self.deck:
                new_card = self.deck.pop()
                self.players[from_player].append(new_card)
                # Sort the player's hand after adding new card
                self.players[from_player].sort()
            
            # Update AI memory with failed ask
            if from_player == 1:
                self.ai_memory['failed_asks'][value] = self.ai_memory['failed_asks'].get(value, 0) + 1
            
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
        if not self.players[1]:
            return False, [], []

        # Update AI memory based on game state
        self._update_ai_memory()

        # Get the best card value to ask for
        best_value = self._get_best_card_to_ask()
        
        # Ask for cards from the human player
        success, cards = self.ask_for_cards(1, 0, best_value)
        
        # Check for sets after the move
        sets = self.check_for_sets(1)
        
        # Handle unsuccessful moves
        if not success:
            if not self.deck:
                self.current_player = 0
                return False, [], sets
            
            # Draw a card if available
            new_card = self.deck.pop()
            self.players[1].append(new_card)
            self.players[1].sort()
            self.current_player = 0
            return False, [new_card], sets

        return success, cards, sets

    def _update_ai_memory(self):
        """Update AI's memory based on current game state"""
        # Update AI's hand in memory
        self.ai_memory['ai_hand'] = set(card.value for card in self.players[1])
        
        # Update deck size in memory
        self.ai_memory['deck_size'] = len(self.deck)
        
        # Update known cards
        self.ai_memory['known_cards'] = (
            self.ai_memory['ai_hand'] |
            self.ai_memory['received_cards'] |
            self.ai_memory['player_received']
        )
        
        # Update card probabilities
        self._update_card_probabilities()
        
        # Increment turn count
        self.ai_memory['turn_count'] += 1

    def _update_card_probabilities(self):
        """Update probability estimates for cards in player's hand"""
        total_cards = len(self.deck) + len(self.players[0]) + len(self.players[1])
        unknown_cards = total_cards - len(self.ai_memory['known_cards'])
        
        # If all cards are known (which shouldn't happen in a real game)
        if unknown_cards == 0:
            # Set all probabilities to 0 since we know all cards
            for value in self.values:
                self.ai_memory['card_probabilities'][value] = 0
            return
        
        for value in self.values:
            if value not in self.ai_memory['known_cards']:
                # Calculate probability based on remaining cards
                remaining_cards = 4 - self.ai_memory['successful_asks'].get(value, 0)
                if remaining_cards > 0:
                    self.ai_memory['card_probabilities'][value] = remaining_cards / unknown_cards
                else:
                    self.ai_memory['card_probabilities'][value] = 0

    def _get_best_card_to_ask(self):
        """Determine the best card value to ask for using multiple strategies"""
        # Strategy 1: Look for cards that would complete sets
        potential_sets = self._find_potential_sets()
        if potential_sets:
            return self._select_best_potential_set(potential_sets)

        # Strategy 2: Ask for cards with high probability
        high_prob_cards = self._get_high_probability_cards()
        if high_prob_cards:
            return high_prob_cards[0]

        # Strategy 3: Ask for cards that AI has multiple of
        multiple_cards = self._get_cards_with_multiple()
        if multiple_cards:
            return self._select_best_multiple_card(multiple_cards)

        # Strategy 4: Ask for cards based on player behavior
        behavior_based = self._get_behavior_based_card()
        if behavior_based:
            return behavior_based

        # Strategy 5: Ask for high-value cards
        return self._get_high_value_card()

    def _select_best_potential_set(self, potential_sets):
        """Select the best potential set to complete based on probability"""
        best_value = None
        best_score = -1
        
        for value in potential_sets:
            # Calculate score based on probability and value
            prob = self.ai_memory['card_probabilities'].get(value, 0)
            value_score = self._get_card_value_score(value)
            score = prob * value_score
            
            if score > best_score:
                best_score = score
                best_value = value
        
        return best_value or potential_sets[0]

    def _get_high_probability_cards(self):
        """Get cards with high probability of being in player's hand"""
        threshold = 0.3  # Probability threshold
        high_prob_cards = [
            value for value, prob in self.ai_memory['card_probabilities'].items()
            if prob > threshold
        ]
        return sorted(high_prob_cards, key=lambda x: self._get_card_value_score(x), reverse=True)

    def _select_best_multiple_card(self, multiple_cards):
        """Select the best card to ask for among multiple cards"""
        return max(multiple_cards, key=lambda x: (
            self.ai_memory['card_probabilities'].get(x, 0) * 
            self._get_card_value_score(x)
        ))

    def _get_behavior_based_card(self):
        """Get card to ask for based on player's behavior patterns"""
        if not self.ai_memory['player_asked_for']:
            return None
            
        # Look for patterns in player's asking behavior
        recent_asks = list(self.ai_memory['player_asked_for'])[-3:]
        if recent_asks:
            # If player has asked for high-value cards recently, they might have them
            if all(self._get_card_value_score(card) > 10 for card in recent_asks):
                return self._get_high_value_card()
            
            # If player has asked for specific suits, they might have more cards of that suit
            for card in recent_asks:
                if self.ai_memory['card_probabilities'].get(card, 0) > 0.2:
                    return card
        
        return None

    def _get_card_value_score(self, value):
        """Calculate the strategic value of a card"""
        value_ranks = {'A': 14, 'K': 13, 'Q': 12, 'J': 11}
        # First check if it's a face card
        if value in value_ranks:
            base_score = value_ranks[value]
        else:
            # If not a face card, convert to int
            base_score = int(value)
        
        # Adjust score based on game state
        if self.ai_memory['deck_size'] < 10:  # Late game
            base_score *= 1.2  # Value high cards more in late game
        
        # Adjust based on successful asks
        success_rate = self.ai_memory['successful_asks'].get(value, 0) / (
            self.ai_memory['successful_asks'].get(value, 0) + 
            self.ai_memory['failed_asks'].get(value, 0) + 1
        )
        
        return base_score * (1 + success_rate)

    def _find_potential_sets(self):
        """Find cards that would complete sets in AI's hand"""
        values_count = {}
        for card in self.players[1]:
            values_count[card.value] = values_count.get(card.value, 0) + 1
        
        # Return values that appear 2 or 3 times (potential for sets)
        return [value for value, count in values_count.items() if 2 <= count <= 3]

    def _get_cards_with_multiple(self):
        """Get cards that AI has multiple of"""
        values_count = {}
        for card in self.players[1]:
            values_count[card.value] = values_count.get(card.value, 0) + 1
        return [value for value, count in values_count.items() if count >= 2]

    def _get_high_value_card(self):
        """Get a high-value card to ask for"""
        value_ranks = {'A': 14, 'K': 13, 'Q': 12, 'J': 11}
        for value in self.values[::-1]:  # Iterate from highest to lowest
            if value not in self.ai_memory['asked_cards']:
                return value
        return self.values[0]  # Fallback to lowest card

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