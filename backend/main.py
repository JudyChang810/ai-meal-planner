from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, TypedDict, Annotated, Optional, Dict, Any
import os
import uvicorn
from dotenv import load_dotenv
import json
import re
from contextlib import asynccontextmanager

# Load environment variables from .env file
load_dotenv()

# Arize and tracing imports
from arize.otel import register
from openinference.instrumentation.langchain import LangChainInstrumentor
from openinference.instrumentation.openai import OpenAIInstrumentor
from openinference.instrumentation.litellm import LiteLLMInstrumentor
from openinference.instrumentation import using_prompt_template
from opentelemetry import trace

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from langchain_core.tools import tool

# LangGraph imports
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from typing_extensions import TypedDict, Annotated
import operator

# Configure LiteLLM
import litellm
litellm.set_verbose = True
litellm.drop_params = True

# Global tracer provider to ensure it's available across the application
tracer_provider = None

# Initialize Arize tracing
def setup_tracing():
    print(">>> setup_tracing() called")
    global tracer_provider
    try:
        # Check if required environment variables are set
        space_id = os.getenv("ARIZE_SPACE_ID")
        api_key = os.getenv("ARIZE_API_KEY")
        
        if not space_id or not api_key or space_id == "your_arize_space_id_here" or api_key == "your_arize_api_key_here":
            print("⚠️ Arize credentials not configured properly.")
            print("📝 Please set ARIZE_SPACE_ID and ARIZE_API_KEY environment variables.")
            print("📝 Copy backend/env_example.txt to backend/.env and update with your credentials.")
            return None
            
        tracer_provider = register(
            space_id=space_id,
            api_key=api_key,
            project_name="meal-planner"
        )
        
        # Only instrument LangChain to avoid duplicate traces
        LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
        
        # Keep LiteLLM instrumentation for direct LiteLLM calls
        LiteLLMInstrumentor().instrument(
            tracer_provider=tracer_provider,
            skip_dep_check=True
        )
        
        print("✅ Arize tracing initialized successfully (LangChain + LiteLLM only)")
        print(f"📊 Project: meal-planner")
        print(f"🔗 Space ID: {space_id[:8]}...")
        
        return tracer_provider
        
    except Exception as e:
        print(f"⚠️ Arize tracing setup failed: {str(e)}")
        print("📝 Continuing without tracing - check your ARIZE_SPACE_ID and ARIZE_API_KEY")
        return None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup tracing before anything else
    setup_tracing()
    yield

# Initialize FastAPI
app = FastAPI(title="Meal Planner API", lifespan=lifespan)

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
    dishCategory: str
    courseType: str

class MealPlanTextResponse(BaseModel):
    result: str

# Initialize the LLM
llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini",
    temperature=0.7,
    max_tokens=1200,
    timeout=30
)

# Define the state for our meal planner graph
class MealPlannerState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    meal_request: Dict[str, Any]
    requirements_analysis: Optional[str]
    dish_recommendations: Optional[str]
    alternative_ingredients: Optional[str]
    final_result: Optional[str]

# Define meal planning tools with proper trace context
@tool
def analyze_meal_requirements(meal_purpose: str, num_people: int, num_dishes: int, cuisine_style: str, dietary_options: str, dish_category: str, course_type: str) -> str:
    """Analyze and structure meal requirements for planning."""
    system_prompt = "You are a meal planning analyst. CRITICAL: Your response must be under 200 words. Analyze requirements and provide structured planning guidance."
    
    prompt_template = """Analyze these meal requirements and provide structured planning guidance:

Purpose: {meal_purpose}
People: {num_people}
Dishes: {num_dishes}
Cuisine: {cuisine_style}
Dietary: {dietary_options}
Category: {dish_category}
Course: {course_type}

Provide:
- Meal planning strategy
- Portion considerations
- Dietary accommodation approach
- Cuisine-specific recommendations
- Course structure guidance"""
    
    prompt_variables = {
        "meal_purpose": meal_purpose,
        "num_people": num_people,
        "num_dishes": num_dishes,
        "cuisine_style": cuisine_style,
        "dietary_options": dietary_options,
        "dish_category": dish_category,
        "course_type": course_type
    }
    
    with using_prompt_template(
        template=prompt_template,
        variables=prompt_variables,
        version="requirements-analysis-v1.0",
    ):
        formatted_prompt = prompt_template.format(**prompt_variables)
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=formatted_prompt)
        ])
    return response.content

@tool
def generate_dishes(meal_requirements: str, cuisine: str, dietary_options: str, num_dishes: int, dish_category: str) -> str:
    """Generate recommended dishes with recipes using LLM."""
    system_prompt = "You are a dish recommendation expert. CRITICAL: Your response must be under 400 words. Focus on practical dishes with complete recipes."
    
    prompt_template = """Generate {num_dishes} dishes with complete recipes based on requirements:

Requirements: {meal_requirements}
Cuisine: {cuisine}
Dietary: {dietary_options}
Category: {dish_category}

For each dish, provide:
- Dish name
- Brief description
- Complete ingredient list with quantities
- Step-by-step cooking instructions

Be practical, specific, and include full recipes with cooking times and techniques."""
    
    prompt_variables = {
        "meal_requirements": meal_requirements,
        "cuisine": cuisine,
        "dietary_options": dietary_options,
        "num_dishes": num_dishes,
        "dish_category": dish_category
    }
    
    with using_prompt_template(
        template=prompt_template,
        variables=prompt_variables,
        version="dishes-llm-v1.0",
    ):
        formatted_prompt = prompt_template.format(**prompt_variables)
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=formatted_prompt)
        ])
    return response.content

@tool
def suggest_alternative_ingredients(dish_recommendations: str, dietary_options: str) -> str:
    """Suggest alternative ingredients for dietary restrictions and substitutions."""
    system_prompt = "You are an ingredient substitution expert. CRITICAL: Your response must be under 300 words. Provide practical alternative ingredients."
    
    prompt_template = """Suggest alternative ingredients for these dishes:

Dishes: {dish_recommendations}
Dietary Requirements: {dietary_options}

For each dish, provide:
- Original ingredients that need substitution
- Alternative ingredients with reasons
- Substitution ratios/quantities
- Cooking adjustments if needed

Focus on practical, accessible alternatives."""
    
    prompt_variables = {
        "dish_recommendations": dish_recommendations,
        "dietary_options": dietary_options
    }
    
    with using_prompt_template(
        template=prompt_template,
        variables=prompt_variables,
        version="alternatives-v1.0",
    ):
        formatted_prompt = prompt_template.format(**prompt_variables)
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=formatted_prompt)
        ])
    return response.content

@tool
def synthesize_meal_plan(meal_requirements: str, dish_recommendations: str, alternative_ingredients: str) -> str:
    """Synthesize all previous results into a final meal plan."""
    system_prompt = (
        "You are a meal plan synthesizer. "
        "For each dish, respond ONLY with a valid, complete JSON array. "
        "Each dish object MUST have the following fields in this exact order: "
        "1. name (string) - The dish name, "
        "2. description (string) - A brief description, "
        "3. ingredients (array of objects with 'item' and 'quantity'), "
        "4. alternativeIngredients (array of objects with 'original' and 'alternative'), "
        "5. recipe (string) - Step-by-step instructions, "
        "6. cookingTips (string) - Any tips for preparation. "
        "Do not include any extra text, markdown, or explanations. "
        "Ensure all strings are properly closed and the JSON is valid. "
        "Example:\n"
        "[{\n"
        "  \"name\": \"Dish Name\",\n"
        "  \"description\": \"...\",\n"
        "  \"ingredients\": [{\"item\": \"...\", \"quantity\": \"...\"}],\n"
        "  \"alternativeIngredients\": [{\"original\": \"...\", \"alternative\": \"...\"}],\n"
        "  \"recipe\": \"...\",\n"
        "  \"cookingTips\": \"...\"\n"
        "}]"
    )
    
    prompt_template = """Create a final meal plan from all gathered information:

Requirements: {meal_requirements}
Dish Recommendations (with recipes): {dish_recommendations}
Alternative Ingredients: {alternative_ingredients}

Create a structured meal plan with:
- Final dish selection
- Complete recipes (cooking steps)
- Ingredient lists with quantities
- Alternative ingredient options
- Cooking tips and timing

Format as JSON array with keys: name, description, recipe, ingredients, alternativeIngredients, cookingTips.
Include complete cooking instructions in the recipe field.
Be practical and complete."""
    
    prompt_variables = {
        "meal_requirements": meal_requirements,
        "dish_recommendations": dish_recommendations,
        "alternative_ingredients": alternative_ingredients
    }
    
    with using_prompt_template(
        template=prompt_template,
        variables=prompt_variables,
        version="synthesis-v1.0",
    ):
        formatted_prompt = prompt_template.format(**prompt_variables)
        response = llm.invoke([
        SystemMessage(content=system_prompt),
            HumanMessage(content=formatted_prompt)
        ])
    return response.content

# Define nodes for the LangGraph workflow
def requirements_node(state: MealPlannerState) -> MealPlannerState:
    """Analyze meal requirements"""
    try:
        meal_req = state["meal_request"]
        print(f"📋 Starting requirements analysis for {meal_req.get('purpose', 'meal planning')}")
        
        requirements_result = analyze_meal_requirements.invoke({
            "meal_purpose": meal_req["purpose"],
            "num_people": meal_req["people"],
            "num_dishes": meal_req["dishes"],
            "cuisine_style": ', '.join(meal_req["cuisines"]) if meal_req["cuisines"] else "General",
            "dietary_options": ', '.join(meal_req["dietaryRestrictions"]) if meal_req["dietaryRestrictions"] else "None",
            "dish_category": meal_req["dishCategory"],
            "course_type": meal_req["courseType"]
        })
        
        print(f"✅ Requirements analysis completed")
        return {
            "messages": [HumanMessage(content=f"Requirements analyzed: {requirements_result}")],
            "requirements_analysis": requirements_result
        }
    except Exception as e:
        print(f"❌ Requirements node error: {str(e)}")
        return {
            "messages": [HumanMessage(content=f"Requirements analysis failed: {str(e)}")],
            "requirements_analysis": f"Requirements analysis failed: {str(e)}"
        }

def dish_generation_node(state: MealPlannerState) -> MealPlannerState:
    """Generate dish recommendations"""
    try:
        meal_req = state["meal_request"]
        requirements_data = state.get("requirements_analysis", "")
        print(f"🍽️ Starting dish generation for {meal_req.get('purpose', 'meal planning')}")
        
        dish_result = generate_dishes.invoke({
            "meal_requirements": requirements_data,
            "cuisine": ', '.join(meal_req["cuisines"]) if meal_req["cuisines"] else "General",
            "dietary_options": ', '.join(meal_req["dietaryRestrictions"]) if meal_req["dietaryRestrictions"] else "None",
            "num_dishes": meal_req["dishes"],
            "dish_category": meal_req["dishCategory"]
        })
        
        print(f"✅ Dish generation completed")
        return {
            "messages": [HumanMessage(content=f"Dishes generated: {dish_result}")],
            "dish_recommendations": dish_result
        }
    except Exception as e:
        print(f"❌ Dish generation node error: {str(e)}")
        return {
            "messages": [HumanMessage(content=f"Dish generation failed: {str(e)}")],
            "dish_recommendations": f"Dish generation failed: {str(e)}"
        }

def alternatives_node(state: MealPlannerState) -> MealPlannerState:
    """Suggest alternative ingredients"""
    try:
        meal_req = state["meal_request"]
        dish_data = state.get("dish_recommendations", "")
        print(f"🔄 Starting alternative ingredients suggestion")
        
        alternatives_result = suggest_alternative_ingredients.invoke({
            "dish_recommendations": dish_data,
            "dietary_options": ', '.join(meal_req["dietaryRestrictions"]) if meal_req["dietaryRestrictions"] else "None"
        })
        
        print(f"✅ Alternative ingredients completed")
        return {
            "messages": [HumanMessage(content=f"Alternatives suggested: {alternatives_result}")],
            "alternative_ingredients": alternatives_result
        }
    except Exception as e:
        print(f"❌ Alternatives node error: {str(e)}")
        return {
            "messages": [HumanMessage(content=f"Alternatives failed: {str(e)}")],
            "alternative_ingredients": f"Alternatives failed: {str(e)}"
        }

def synthesis_node(state: MealPlannerState) -> MealPlannerState:
    """Synthesize final meal plan"""
    try:
        print(f"📝 Starting meal plan synthesis")
        
        # Get data from previous nodes
        requirements_data = state.get("requirements_analysis", "")
        dish_data = state.get("dish_recommendations", "")
        alternatives_data = state.get("alternative_ingredients", "")
        
        print(f"📊 Data available - Requirements: {len(requirements_data) if requirements_data else 0} chars, Dishes: {len(dish_data) if dish_data else 0} chars, Alternatives: {len(alternatives_data) if alternatives_data else 0} chars")
        
        synthesis_result = synthesize_meal_plan.invoke({
            "meal_requirements": requirements_data,
            "dish_recommendations": dish_data,
            "alternative_ingredients": alternatives_data
        })
        
        print(f"✅ Meal plan synthesis completed")
        return {
            "messages": [HumanMessage(content=synthesis_result)],
            "final_result": synthesis_result
        }
    except Exception as e:
        print(f"❌ Synthesis node error: {str(e)}")
        return {
            "messages": [HumanMessage(content=f"Meal plan synthesis failed: {str(e)}")],
            "final_result": f"Meal plan synthesis failed: {str(e)}"
        }

# Build the meal planning graph
def create_meal_planning_graph():
    """Create and compile the meal planning graph"""
    
    # Create the state graph
    workflow = StateGraph(MealPlannerState)
    
    # Add nodes
    workflow.add_node("requirements", requirements_node)
    workflow.add_node("dish_generation", dish_generation_node)
    workflow.add_node("alternatives", alternatives_node)
    workflow.add_node("synthesis", synthesis_node)
    
    # Set up the workflow sequence
    workflow.set_entry_point("requirements")
    workflow.add_edge("requirements", "dish_generation")
    workflow.add_edge("dish_generation", "alternatives")
    workflow.add_edge("alternatives", "synthesis")
    workflow.add_edge("synthesis", END)
    
    # Compile with memory
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)

@app.post("/plan_meal", response_model=MealPlanTextResponse)
async def plan_meal(request: MealPlanRequest):
    """Plan a meal using LangGraph workflow and return plain text result."""
    try:
        # Create the meal planning graph
        graph = create_meal_planning_graph()
        # Prepare initial state
        initial_state = {
            "messages": [],
            "meal_request": request.model_dump(),
            "requirements_analysis": None,
            "dish_recommendations": None,
            "alternative_ingredients": None,
            "final_result": None
        }
        # Execute the workflow
        config = {"configurable": {"thread_id": f"meal_{request.purpose.replace(' ', '_')}_{request.people}_{request.dishes}"}}
        print(f"🚀 Starting meal planning for {request.purpose} ({request.people} people, {request.dishes} dishes)")
        output = graph.invoke(initial_state, config)
        print(f"✅ Meal planning completed. Output keys: {list(output.keys()) if output else 'None'}")
        # Extract the final result as plain text
        if output and output.get("final_result"):
            final_meal_plan = output.get("final_result")
        elif output and output.get("messages") and len(output.get("messages")) > 0:
            last_message = output.get("messages")[-1]
            final_meal_plan = last_message.content if hasattr(last_message, 'content') else str(last_message)
        else:
            final_meal_plan = "Meal planning completed but no detailed results available."
        return MealPlanTextResponse(result=final_meal_plan)
    except Exception as e:
        print(f"❌ Meal planning error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Meal planning failed: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Meal Planner API is running with LangGraph workflow!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "meal-planner-backend"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
