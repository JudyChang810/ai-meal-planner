export interface Ingredient {
  ingredient: string;
  quantity: string;
}

export interface AlternativeIngredient {
  original: string;
  alternative: string;
}

export interface Dish {
  name: string;
  description: string;
  recipe: string;
  ingredients: Ingredient[];
  alternativeIngredients: AlternativeIngredient[];
  cookingTips?: string;
  imageUrl?: string;
}

export interface MealPlanRequest {
  purpose: string;
  people: number;
  dishes: number;
  cuisines: string[];
  dietaryRestrictions: string[];
  dishCategory: string;
  courseType: string;
}

export interface MealPlanResult {
  dishes: Dish[];
} 