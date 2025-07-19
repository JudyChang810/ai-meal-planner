# AI Meal Planner

A fast, customizable meal planning application powered by React, FastAPI, and OpenAI.

## Features

- **Personalized Meal Planning:** Generate meal plans for any purpose (e.g., family dinner, party, special diet).
- **Customizable Options:** Specify number of people, number of dishes, dish categories, course types, preferred cuisines, and dietary restrictions.
- **Diverse Cuisine Support:** Choose from popular cuisines or mix and match.
- **Dietary Flexibility:** Vegan, vegetarian, low-carb, dairy-free, nut-free, gluten-free, and more.
- **Detailed Recipes:** Each dish includes a recipe, main ingredients, and alternative ingredients for dietary needs.
- **AI-Powered Backend:** Uses OpenAI's GPT-4o-mini for creative, high-quality meal suggestions.

## Architecture

### Frontend (React + TypeScript)
- User-friendly UI for meal planning input
- Displays recommended dishes and recipes
- Handles loading and error states

### Backend (FastAPI + OpenAI)
- `/plan_meal` endpoint accepts meal planning requests
- Uses OpenAI LLM to generate meal plans and recipes
- Returns structured JSON with dish details

## Quick Start

### 1. Setup Environment

Create a `.env` file in the `backend/` directory:

```bash
OPENAI_API_KEY=your_openai_api_key
```

### 2. Install Dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 3. Run the Application

```bash
# Start both services
./start.sh

# Or run separately:
# Backend: cd backend && python main.py
# Frontend: cd frontend && npm start
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## How It Works

1. **Fill out the meal planner form** with your preferences (purpose, people, dishes, cuisines, dietary needs, etc.).
2. **Submit the form** to generate a meal plan.
3. **View the results:** See recommended dishes, ingredients, alternative ingredients, and step-by-step recipes.

## Tech Stack

- **Frontend:** React, TypeScript
- **Backend:** FastAPI, OpenAI (GPT-4o-mini)
- **Infrastructure:** Docker, Docker Compose (optional)

## API Endpoint

### POST `/plan_meal`
Creates a personalized meal plan.

**Request Example:**
```json
{
  "purpose": "Family dinner",
  "people": 4,
  "dishes": 3,
  "cuisines": ["Italian", "French"],
  "dietaryRestrictions": ["Vegetarian"]
}
```

**Response Example:**
```json
{
  "dishes": [
    {
      "name": "Vegetarian Lasagna",
      "recipe": "Step 1: ... Step 2: ...",
      "ingredients": ["pasta", "cheese", "tomato sauce"],
      "alternativeIngredients": ["vegan cheese"],
      "imageUrl": ""
    },
    ...
  ]
}
```

## Project History

This project was originally based on [amank94/ai-trip-planner](https://github.com/amank94/ai-trip-planner).
The `main` branch contains the original code, and the `ai-meal-planner` branch contains my custom meal planner agent.
