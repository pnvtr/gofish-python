import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = 'http://localhost:5000/api';

function App() {
  const [gameState, setGameState] = useState(null);
  const [selectedCard, setSelectedCard] = useState(null);
  const [message, setMessage] = useState('');
  const [isAITurn, setIsAITurn] = useState(false);

  useEffect(() => {
    startNewGame();
  }, []);

  useEffect(() => {
    if (gameState && gameState.current_player === 1) {
      handleAITurn();
    }
  }, [gameState]);

  const startNewGame = async () => {
    try {
      const response = await axios.post(`${API_URL}/new-game`);
      setGameState(response.data);
      setMessage('Game started! Your turn.');
      setIsAITurn(false);
      setSelectedCard(null);
    } catch (error) {
      setMessage('Error starting game');
      console.error(error);
    }
  };

  const handleCardSelect = (card) => {
    if (gameState.current_player === 0) {
      setSelectedCard(card);
    }
  };

  const handleAITurn = async () => {
    setIsAITurn(true);
    try {
      const response = await axios.post(`${API_URL}/ai-move`);
      const newState = response.data;
      setGameState(newState);

      if (newState.error) {
        setMessage(newState.error);
        return;
      }

      if (newState.success) {
        setMessage(`AI got ${newState.cards.length} card(s) from you!`);
      } else {
        setMessage('AI went fishing!');
      }

      if (newState.sets.length > 0) {
        setMessage(`AI completed set(s) of ${newState.sets.join(', ')}!`);
      }

      if (newState.game_over) {
        setMessage(`Game Over! ${newState.winner === 1 ? 'AI' : 'You'} wins!`);
      }

      setIsAITurn(false);
    } catch (error) {
      setMessage(error.response?.data?.error || 'Error during AI turn');
      console.error(error);
      setIsAITurn(false);
    }
  };

  const handleAskForCards = async () => {
    if (!selectedCard || !gameState || gameState.current_player !== 0) return;

    try {
      const response = await axios.post(`${API_URL}/ask-cards`, {
        from_player: 0,
        to_player: 1,
        value: selectedCard.split(' ')[0]
      });

      const newState = response.data;
      
      if (newState.error) {
        setMessage(newState.error);
        return;
      }

      setGameState(newState);

      if (newState.success) {
        setMessage(`Successfully got ${newState.cards.length} card(s)!`);
      } else {
        setMessage('Go Fish!');
      }

      if (newState.sets.length > 0) {
        setMessage(`Completed set(s) of ${newState.sets.join(', ')}!`);
      }

      if (newState.game_over) {
        setMessage(`Game Over! ${newState.winner === 0 ? 'You' : 'AI'} wins!`);
      }

      setSelectedCard(null);
    } catch (error) {
      setMessage(error.response?.data?.error || 'Error making move');
      console.error(error);
    }
  };

  const renderPlayerHand = () => {
    if (!gameState) return null;
    const hand = gameState.player1_hand;
    return (
      <div className="player-hand">
        <h3>Your Hand</h3>
        <div className="cards">
          {hand.map((card, index) => (
            <div
              key={index}
              className={`card ${selectedCard === card ? 'selected' : ''} ${
                gameState.current_player === 0 ? 'clickable' : ''
              }`}
              onClick={() => handleCardSelect(card)}
            >
              {card}
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="App">
      <h1>Go Fish</h1>
      <div className="score-board">
        <div className="score">
          <span>Your Books: {gameState?.books[0] || 0}</span>
        </div>
        <div className="score">
          <span>AI Books: {gameState?.books[1] || 0}</span>
        </div>
      </div>
      <button onClick={startNewGame}>New Game</button>
      {message && <div className="message">{message}</div>}
      {isAITurn && <div className="message">AI is thinking...</div>}
      {gameState && (
        <>
          <div className="ai-hand">
            <h3>AI's Hand</h3>
            <div className="cards">
              {gameState.player2_hand.map((_, index) => (
                <div key={index} className="card hidden">
                  🂠
                </div>
              ))}
            </div>
          </div>
          {renderPlayerHand()}
          {selectedCard && gameState.current_player === 0 && (
            <button onClick={handleAskForCards}>
              Ask for Cards
            </button>
          )}
        </>
      )}
    </div>
  );
}

export default App; 