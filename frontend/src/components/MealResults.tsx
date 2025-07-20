import React from 'react';

interface Dish {
  name: string;
  description: string;
  ingredients: { item: string; quantity: string }[];
  alternativeIngredients: { original: string; alternative: string }[];
  recipe: string;
  cookingTips: string;
}

interface Props {
  result: string;
}

const MealResults: React.FC<Props> = ({ result }) => {
  let dishes: Dish[] | null = null;
  try {
    const parsed = JSON.parse(result);
    if (Array.isArray(parsed)) {
      dishes = parsed;
    }
  } catch {
    // Not valid JSON, will display as plain text
  }

  if (dishes) {
    return (
      <div>
        <h3>Recommended Dishes</h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '2rem', justifyContent: 'center' }}>
          {dishes.map((dish, idx) => (
            <div key={idx} style={{ border: '1px solid #ccc', borderRadius: 8, padding: 16, width: 340, background: '#fff' }}>
              <h4>{dish.name}</h4>
              {dish.description && <p style={{ fontStyle: 'italic', color: '#555', marginTop: 0 }}>{dish.description}</p>}
              <div style={{ textAlign: 'left' }}>
                <strong>Ingredients</strong>
                <ul>
                  {dish.ingredients.map((item, i) => (
                    <li key={i}>
                      {item.item}
                      {item.quantity ? ` (${item.quantity})` : ''}
                    </li>
                  ))}
                </ul>
                <strong>Alternative Ingredients</strong>
                <ul>
                  {dish.alternativeIngredients.map((item, i) => (
                    <li key={i}>
                      {item.original} → {item.alternative}
                    </li>
                  ))}
                </ul>
                <strong>Recipe</strong>
                <p>{dish.recipe}</p>
                {dish.cookingTips && (
                  <div style={{ marginTop: 8 }}>
                    <strong>Cooking Tips:</strong>
                    <div style={{ color: '#3a3', fontStyle: 'italic', marginTop: 2 }}>{dish.cookingTips}</div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Fallback: display as plain text
  return (
    <div>
      <h3>Recommended Dishes</h3>
      <div style={{ whiteSpace: 'pre-line', textAlign: 'left', margin: '0 auto', maxWidth: 700, background: '#fff', borderRadius: 8, padding: 24, border: '1px solid #eee' }}>
        {result}
      </div>
    </div>
  );
};

export default MealResults; 