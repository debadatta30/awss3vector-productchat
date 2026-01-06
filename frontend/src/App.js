import React, { useState } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = 'https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod/chat';

function App() {
  const [messages, setMessages] = useState([
    { type: 'bot', text: 'Hi! I\'m your product assistant. Ask me about any product you\'re looking for!' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { type: 'user', text: input };
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await axios.post(API_URL, {
        question: input
      });

      const botMessage = {
        type: 'bot',
        text: response.data.answer,
        product: response.data.product,
        confidence: response.data.confidence,
        foundProduct: response.data.found_product
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = {
        type: 'bot',
        text: 'Sorry, I encountered an error. Please try again.',
        error: true
      };
      setMessages(prev => [...prev, errorMessage]);
    }

    setInput('');
    setLoading(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>🛍️ Product Chat</h1>
        <p>Find products with AI assistance</p>
      </header>

      <div className="chat-container">
        <div className="messages">
          {messages.map((message, index) => (
            <div key={index} className={`message ${message.type}`}>
              <div className="message-content">
                {message.text}
                
                {message.product && (
                  <div className="product-card">
                    <h3>{message.product.name}</h3>
                    <p className="category">{message.product.category}</p>
                    <p className="price">${message.product.price}</p>
                    <p className="confidence">Confidence: {message.confidence * 100}%</p>
                  </div>
                )}
                
                {message.confidence && !message.foundProduct && (
                  <p className="low-confidence">
                    No exact match found (confidence: {message.confidence * 100}%)
                  </p>
                )}
              </div>
            </div>
          ))}
          
          {loading && (
            <div className="message bot">
              <div className="message-content">
                <div className="typing">Searching products...</div>
              </div>
            </div>
          )}
        </div>

        <div className="input-container">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about any product..."
            disabled={loading}
          />
          <button onClick={sendMessage} disabled={loading || !input.trim()}>
            Send
          </button>
        </div>
      </div>

      <div className="suggestions">
        <p>Try asking:</p>
        <div className="suggestion-buttons">
          <button onClick={() => setInput('Show me wireless headphones')}>
            Wireless headphones
          </button>
          <button onClick={() => setInput('I need a fitness tracker')}>
            Fitness tracker
          </button>
          <button onClick={() => setInput('Gaming mouse with RGB')}>
            Gaming mouse
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;