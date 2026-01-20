import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, BarChart2, RotateCcw, Check, X, Trophy } from 'lucide-react';
import './App.css';
import rawVerbs from './verbs.json';

// --- Game Logic Hooks ---

function useGameLogic() {
  const [deck, setDeck] = useState([]);
  const [currentCard, setCurrentCard] = useState(null);
  const [options, setOptions] = useState([]);
  const [gameState, setGameState] = useState('menu'); // menu, playing, feedback, stats
  const [score, setScore] = useState(0);
  const [streak, setStreak] = useState(0);
  const [feedback, setFeedback] = useState(null); // 'correct' or 'wrong'

  // Load progress from localStorage on mount
  useEffect(() => {
    const savedProgress = JSON.parse(localStorage.getItem('verb_progress') || '{}');

    // Merge raw verbs with saved progress
    const mergedDeck = rawVerbs.map(verb => {
      const saved = savedProgress[verb.id];
      if (saved) {
        return { ...verb, ...saved };
      }
      return {
        ...verb,
        weight: 100,
        correct_count: 0,
        next_review: 0
      };
    });

    setDeck(mergedDeck);
  }, []);

  // Save progress
  const saveProgress = (updatedCard) => {
    const savedProgress = JSON.parse(localStorage.getItem('verb_progress') || '{}');
    savedProgress[updatedCard.id] = {
      weight: updatedCard.weight,
      correct_count: updatedCard.correct_count,
      next_review: updatedCard.next_review,
      last_reviewed: updatedCard.last_reviewed
    };
    localStorage.setItem('verb_progress', JSON.stringify(savedProgress));
  };

  const getNextCard = () => {
    if (deck.length === 0) return null;

    const now = Date.now() / 1000; // Unix timestamp in seconds

    // 1. Due Cards (SRS)
    const dueCards = deck.filter(c => c.next_review <= now);
    let selected = null;

    if (dueCards.length > 0) {
      // Pick random weighted
      selected = dueCards[Math.floor(Math.random() * dueCards.length)];
    } else {
      // 2. New Cards (unseen)
      const newCards = deck.filter(c => c.correct_count === 0);
      if (newCards.length > 0) {
        selected = newCards[Math.floor(Math.random() * Math.min(newCards.length, 10))];
      } else {
        // 3. Fallback: random weighted
        selected = deck[Math.floor(Math.random() * deck.length)];
      }
    }

    return selected;
  };

  const generateOptions = (correctCard) => {
    const candidates = deck.filter(c => c.id !== correctCard.id);
    const shuffledCandidates = [...candidates].sort(() => 0.5 - Math.random());
    const distractors = shuffledCandidates.slice(0, 3).map(c => c.turkish);
    const allOptions = [...distractors, correctCard.turkish];
    return allOptions.sort(() => 0.5 - Math.random());
  };

  const startGame = () => {
    const next = getNextCard();
    if (next) {
      setCurrentCard(next);
      setOptions(generateOptions(next));
      setGameState('playing');
      setFeedback(null);
    }
  };

  const nextCard = () => {
    const next = getNextCard();
    setCurrentCard(next);
    setOptions(generateOptions(next));
    setFeedback(null);
  };

  const handleAnswer = (answer) => {
    if (!currentCard || feedback) return; // Prevent double answering

    const isCorrect = answer === currentCard.turkish;
    const now = Date.now() / 1000;

    let updatedCard = { ...currentCard, last_reviewed: now };

    if (isCorrect) {
      updatedCard.correct_count += 1;
      // SRS Interval
      let interval = 60; // 1 min default
      if (updatedCard.correct_count === 2) interval = 600;
      else if (updatedCard.correct_count === 3) interval = 86400;
      else if (updatedCard.correct_count > 3) interval = 86400 * Math.pow(2, updatedCard.correct_count - 3);

      updatedCard.next_review = now + interval;
      updatedCard.weight = Math.max(1, updatedCard.weight * 0.5);

      setScore(s => s + 10);
      setStreak(s => s + 1);
      setFeedback('correct');
    } else {
      updatedCard.correct_count = 0;
      updatedCard.next_review = now;
      updatedCard.weight = 100;

      setStreak(0);
      setFeedback('wrong');
    }

    // Update deck state
    const newDeck = deck.map(c => c.id === updatedCard.id ? updatedCard : c);
    setDeck(newDeck);

    // Save to local storage
    saveProgress(updatedCard);

    // Removed auto timeout. User must now click to proceed.
  };

  const getStats = () => {
    const learned = deck.filter(c => c.correct_count >= 5).length;
    const inProgress = deck.filter(c => c.correct_count > 0 && c.correct_count < 5).length;
    const newCards = deck.filter(c => c.correct_count === 0).length;
    return { total: deck.length, learned, inProgress, newCards };
  };

  return {
    deck, currentCard, options, gameState, setGameState,
    score, streak, feedback, handleAnswer, startGame, getStats, nextCard
  };
}

// --- Components ---

function Menu({ onStart, onStats, totalWords }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center gap-6 w-full"
    >
      <div className="glass-panel p-8 w-full max-w-sm mb-6">
        <h1>Word Master</h1>
        <p className="opacity-70">Master English Verbs</p>
        <div className="mt-4 text-sm bg-black/20 rounded-full px-4 py-1 inline-block">
          📚 {totalWords} words loaded
        </div>
      </div>

      <button onClick={onStart} className="glass-button text-xl px-8 py-4 rounded-xl w-full max-w-xs flex items-center justify-center gap-3 font-bold group">
        <Play size={24} className="group-hover:fill-current" />
        START GAME
      </button>

      <button onClick={onStats} className="glass-button text-lg px-8 py-3 rounded-xl w-full max-w-xs flex items-center justify-center gap-3">
        <BarChart2 size={20} />
        STATISTICS
      </button>
    </motion.div>
  );
}

function GameCard({ card, options, onAnswer, onNext, feedback, score, streak }) {
  if (!card) return <div>Loading...</div>;

  return (
    <div className="w-full max-w-md mx-auto">
      {/* HUD */}
      <div className="flex justify-between items-center mb-6 px-2">
        <div className="flex items-center gap-2 text-cyan-300">
          <Trophy size={18} />
          <span className="font-bold">{score}</span>
        </div>
        <div className="flex items-center gap-1 text-orange-300">
          <span className="text-xs uppercase tracking-widest opacity-70">Streak</span>
          <span className="font-bold text-lg">🔥 {streak}</span>
        </div>
      </div>

      {/* Main Card */}
      <motion.div
        key={card.id}
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", bounce: 0.5 }}
        className="glass-panel p-8 mb-6 min-h-[200px] flex flex-col justify-center items-center relative overflow-hidden"
      >
        <span className="card-category text-xs bg-white/10 px-3 py-1 rounded-full mb-4">
          {card.category}
        </span>
        <h2 className="card-title text-4xl mb-4">{card.verb}</h2>

        {/* Feedback Overlay */}
        <AnimatePresence>
          {feedback && (
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={onNext} // Continue on click
              className={`absolute inset-0 flex flex-col items-center justify-center bg-black/80 backdrop-blur-sm z-10 cursor-pointer
                ${feedback === 'correct' ? 'text-green-400' : 'text-red-400'}`}
            >
              {feedback === 'correct' ? <Check size={64} /> : <X size={64} />}
              <p className="mt-4 text-white text-center px-4 italic opacity-90">
                "{card.sentence}"
              </p>
              {feedback === 'wrong' && (
                <div className="mt-2 text-white font-bold">
                  {card.turkish}
                </div>
              )}
              <div className="mt-8 text-sm text-white/50 animate-pulse">
                Tap anywhere to continue
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>

      {/* Options */}
      <div className="options-grid">
        {options.map((option, idx) => (
          <motion.button
            key={idx}
            whileTap={{ scale: 0.98 }}
            disabled={feedback !== null}
            onClick={() => onAnswer(option)}
            className={`option-btn ${feedback && option === card.turkish ? 'correct' : ''
              } ${feedback === 'wrong' && feedback !== null ? 'opacity-50' : ''
              }`}
          >
            {option}
          </motion.button>
        ))}
      </div>

      <button
        onClick={() => window.location.reload()}
        className="mt-8 text-white/30 hover:text-white/80 text-sm flex items-center justify-center gap-2 mx-auto"
      >
        <RotateCcw size={14} /> Quit Game
      </button>
    </div>
  );
}

function Stats({ stats, onBack }) {
  return (
    <motion.div
      initial={{ x: 300, opacity: 0 }} animate={{ x: 0, opacity: 1 }}
      className="w-full max-w-sm"
    >
      <div className="glass-panel p-6 mb-6">
        <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
          <BarChart2 /> Statistics
        </h2>

        <div className="space-y-4">
          <StatRow label="Total Words" value={stats.total} color="bg-gray-500" />
          <StatRow label="Learned (Mastered)" value={stats.learned} color="bg-green-500" />
          <StatRow label="In Progress" value={stats.inProgress} color="bg-yellow-500" />
          <StatRow label="New (Unseen)" value={stats.newCards} color="bg-blue-500" />
        </div>

        <div className="mt-6 pt-6 border-t border-white/10">
          <div className="flex justify-between items-center">
            <span>Mastery</span>
            <span className="font-bold text-green-400">
              {((stats.learned / stats.total) * 100).toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-gray-700 h-2 rounded-full mt-2 overflow-hidden">
            <div
              className="bg-green-500 h-full"
              style={{ width: `${(stats.learned / stats.total) * 100}%` }}
            />
          </div>
        </div>
      </div>

      <button onClick={onBack} className="glass-button w-full py-3 rounded-xl font-bold">
        BACK TO MENU
      </button>
    </motion.div>
  );
}

function StatRow({ label, value, color }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className={`w-3 h-3 rounded-full ${color}`} />
        <span className="opacity-80">{label}</span>
      </div>
      <span className="font-bold text-xl">{value}</span>
    </div>
  );
}

// --- Main App ---

function App() {
  const game = useGameLogic();

  return (
    <div className="app-container">
      <AnimatePresence mode="wait">
        {game.gameState === 'menu' && (
          <Menu
            key="menu"
            totalWords={game.deck.length}
            onStart={game.startGame}
            onStats={() => game.setGameState('stats')}
          />
        )}

        {game.gameState === 'playing' && (
          <GameCard
            key="game"
            card={game.currentCard}
            options={game.options}
            onAnswer={game.handleAnswer}
            onNext={game.nextCard}
            feedback={game.feedback}
            score={game.score}
            streak={game.streak}
          />
        )}

        {game.gameState === 'stats' && (
          <Stats
            key="stats"
            stats={game.getStats()}
            onBack={() => game.setGameState('menu')}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;
