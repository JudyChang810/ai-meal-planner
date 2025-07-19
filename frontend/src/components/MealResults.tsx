import React from 'react';
import { MealPlanResult } from '../types/meal';

interface Props {
  results: MealPlanResult;
}

const splitRecipeSteps = (recipe: string) => {
  // Split on period followed by space or end of string, but keep abbreviations together
  return recipe.split(/\.(?!\d|\s*\w\.)\s*/).filter(Boolean);
};

const MealResults: React.FC<Props> = ({ results }) => (
  <div style={{ fontFamily: "Georgia, 'Times New Roman', serif" }}>
    <h3>Recommended Dishes</h3>
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '2rem', justifyContent: 'center' }}>
      {results.dishes.map((dish, idx) => (
        <div key={idx} style={{ border: '1px solid #ccc', borderRadius: 8, padding: 16, width: 320 }}>
          <h4>{dish.name}</h4>
          {/* <img src={dish.imageUrl} alt={dish.name} style={{ width: '100%', borderRadius: 4 }} /> */}
          <div style={{ textAlign: 'left' }}>
            <strong>Ingredients</strong>
            <ul style={{ marginTop: 4, marginBottom: 8 }}>
              {dish.ingredients.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
            <strong>Alternative Ingredients</strong>
            <ul style={{ marginTop: 4, marginBottom: 8 }}>
              {dish.alternativeIngredients.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
            <strong>Recipe</strong>
            {splitRecipeSteps(dish.recipe).length > 1 ? (
              <ol style={{ marginTop: 4 }}>
                {splitRecipeSteps(dish.recipe).map((step, i) => (
                  <li key={i}>{step.trim()}{step.trim().endsWith('.') ? '' : '.'}</li>
                ))}
              </ol>
            ) : (
              <p style={{ marginTop: 4 }}>{dish.recipe}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  </div>
);

export default MealResults; 