export interface MealPlanRequest {
  purpose: string;
  people: number;
  dishes: number;
  cuisines: string[];
  dietaryRestrictions: string[];
}

export interface Dish {
  name: string;
  recipe: string;
  ingredients: string[];
  alternativeIngredients: string[];
  imageUrl: string;
}

export interface MealPlanResult {
  dishes: Dish[];
} 