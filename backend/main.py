from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
import uvicorn
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv()

# LangChain and OpenAI imports
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Initialize FastAPI
app = FastAPI(title="Meal Planner API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class MealPlanRequest(BaseModel):
    purpose: str
    people: int
    dishes: int
    cuisines: List[str]
    dietaryRestrictions: List[str]

class Dish(BaseModel):
    name: str
    recipe: str
    ingredients: List[str]
    alternativeIngredients: List[str]
    imageUrl: str

class MealPlanResponse(BaseModel):
    dishes: List[Dish]

# Initialize the LLM
llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini",
    temperature=0.7,
    max_tokens=1200,
    timeout=30
)

# Helper to generate meal plan using LLM
def generate_meal_plan(request: MealPlanRequest) -> List[Dish]:
    # Prompt the LLM to generate dishes, recipes, ingredients, and alternatives
    system_prompt = (
        "You are an expert meal planner and chef. Given the user's meal purpose, number of people, number of dishes, preferred cuisines, and dietary restrictions, "
        "generate a list of unique dishes. For each dish, provide: 1) the dish name, 2) a short recipe, 3) a list of main ingredients, 4) a list of alternative ingredients for dietary needs. "
        "Respond ONLY with a valid JSON array of objects with keys: name, recipe, ingredients, alternativeIngredients. No explanation or extra text."
    )
    user_prompt = (
        f"Purpose: {request.purpose}\n"
        f"People: {request.people}\n"
        f"Dishes: {request.dishes}\n"
        f"Cuisines: {', '.join(request.cuisines)}\n"
        f"Dietary Restrictions: {', '.join(request.dietaryRestrictions)}"
    )
        response = llm.invoke([
            SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])
    print("LLM raw response:", response.content)  # Debug print
    import json
    import re
    try:
        raw = response.content.strip()
        # Remove Markdown code block if present
        if raw.startswith('```'):
            raw = re.sub(r'^```[a-zA-Z]*\n?', '', raw)
            raw = re.sub(r'```$', '', raw)
            raw = raw.strip()
        dishes_data = json.loads(raw)
        dishes = []
        for dish in dishes_data[:request.dishes]:
            # image_url = generate_dish_image(dish['name'], request.cuisines[0] if request.cuisines else "")
            # Use an empty string or placeholder for imageUrl since AI image generation is disabled
            image_url = ""
            dishes.append(Dish(
                name=dish['name'],
                recipe=dish['recipe'],
                ingredients=dish['ingredients'],
                alternativeIngredients=dish['alternativeIngredients'],
                imageUrl=image_url
            ))
        return dishes
    except Exception as e:
        print(f"Meal plan LLM parsing error: {e}")
        print("LLM response that failed to parse:", response.content)
        # Return a user-friendly error message as a single Dish
        return [Dish(
            name="Meal Plan Error",
            recipe="Sorry, we couldn't generate a meal plan. Please try again or adjust your preferences.",
            ingredients=[],
            alternativeIngredients=[],
            # imageUrl="https://placehold.co/400x300?text=Error"
            imageUrl=""
        )]

@app.post("/plan_meal", response_model=MealPlanResponse)
async def plan_meal(request: MealPlanRequest):
    try:
        dishes = generate_meal_plan(request)
        return MealPlanResponse(dishes=dishes)
    except Exception as e:
        print(f"Meal planning error: {e}")
        raise HTTPException(status_code=500, detail="Meal planning failed.")

@app.get("/")
async def root():
    return {"message": "Meal Planner API is running!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
