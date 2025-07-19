import React, { useState } from 'react';
import MealPlannerForm from './components/MealPlannerForm';
import MealResults from './components/MealResults';
import { MealPlanResult } from './types/meal';
import './App.css';

function App() {
  const [results, setResults] = useState<MealPlanResult | null>(null);

  return (
    <div className="App">
      <header className="meal-header">
        <h1>Plan Your Meals with Ease</h1>
        <p className="meal-header-subtitle">
          Create personalized meal plans and get inspired by delicious recipes.
        </p>
      </header>
      <div className="feature-row meal-feature-row">
        <div className="feature-card meal-feature-card">
          <span role="img" aria-label="Cuisine" className="feature-icon">🍽️</span>
          <h3>Cuisine</h3>
          <p>Explore dishes across global cooking styles</p>
        </div>
        <div className="feature-card meal-feature-card">
          <span role="img" aria-label="Dishes" className="feature-icon">🥗</span>
          <h3>Dishes</h3>
          <p>Create balanced meals with multiple courses</p>
        </div>
        <div className="feature-card meal-feature-card">
          <span role="img" aria-label="Diet" className="feature-icon">🌱</span>
          <h3>Diet</h3>
          <p>Adapt meals to match your dietary needs</p>
        </div>
        <div className="feature-card meal-feature-card">
          <span role="img" aria-label="Inspiration" className="feature-icon">📸</span>
          <h3>Inspiration</h3>
          <p>Discover new dishes and creative ingredient ideas</p>
        </div>
      </div>
      <main className="main-content">
        <div className="form-card">
          <MealPlannerForm setResults={setResults} />
        </div>
        <div className="results-card">
          {results ? (
            <MealResults results={results} />
          ) : (
            <div className="results-placeholder meal-results-placeholder">
              <span className="results-subtext meal-results-subtext">
                The AI Meal Planner will analyze your preferences and create the perfect meal plan
              </span>
            </div>
              )}
        </div>
      </main>
    </div>
  );
}

export default App;
