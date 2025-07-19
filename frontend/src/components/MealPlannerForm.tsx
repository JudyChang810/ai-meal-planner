import React, { useState } from 'react';
import { MealPlanRequest, MealPlanResult } from '../types/meal';

const CUISINES = ['Thai', 'Italian', 'Japanese', 'Mexican', 'Indian', 'French', 'Chinese', 'American'];
const DIETS = ['Vegan', 'Vegetarian', 'Low-Carb', 'Dairy-Free', 'Nut-Free', 'Gluten-Free'];

interface MealPlannerFormProps {
  setResults: (results: MealPlanResult) => void;
}

// Define form state type explicitly
interface MealPlannerFormState {
  purpose: string;
  dishCategory: string;
  courseType: string;
  people: string;
  dishes: string;
  cuisines: string;
  dietaryRestrictions: string;
}

const MAX_PEOPLE = 15;
const MAX_DISHES = 15;

const MealPlannerForm: React.FC<MealPlannerFormProps> = ({ setResults }) => {
  const [form, setForm] = useState<MealPlannerFormState>({
    purpose: '',
    dishCategory: '',
    courseType: '',
    people: '1',
    dishes: '1',
    cuisines: '',
    dietaryRestrictions: '',
  });
  const [loading, setLoading] = useState(false);
  const [peopleError, setPeopleError] = useState('');
  const [dishesError, setDishesError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    if (name === 'people') {
      if (Number(value) > MAX_PEOPLE) {
        setPeopleError(`Maximum allowed is ${MAX_PEOPLE}.`);
        return;
      } else {
        setPeopleError('');
      }
    }
    if (name === 'dishes') {
      if (Number(value) > MAX_DISHES) {
        setDishesError(`Maximum allowed is ${MAX_DISHES}.`);
        return;
      } else {
        setDishesError('');
      }
    }
    setForm(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleMultiSelect = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const { name, options } = e.target;
    const values = Array.from(options).filter(o => o.selected).map(o => o.value);
    setForm(prev => ({ ...prev, [name]: values }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResults(null as any); // Clear previous results
    try {
      // Prepare payload with correct types for backend
      const payload: MealPlanRequest & { dishCategory?: string; courseType?: string } = {
        purpose: form.purpose,
        people: Number(form.people),
        dishes: Number(form.dishes),
        cuisines: form.cuisines
          ? form.cuisines.split(',').map(s => s.trim()).filter(Boolean)
          : [],
        dietaryRestrictions: form.dietaryRestrictions
          ? form.dietaryRestrictions.split(',').map(s => s.trim()).filter(Boolean)
          : [],
        dishCategory: form.dishCategory,
        courseType: form.courseType,
      };
      const res = await fetch('/plan_meal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      setResults(data);
    } catch (err) {
      alert('Failed to generate meal plan.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="meal-form" onSubmit={handleSubmit}>
      <label className="meal-form-label">
        Purpose
        <input
          className="meal-form-input"
          name="purpose"
          value={form.purpose}
          onChange={handleChange}
          required
        />
      </label>
      <label className="meal-form-label">
        Number of People
        <input
          className="meal-form-input"
          name="people"
          type="number"
          min={1}
          value={form.people}
          onChange={handleChange}
          required
        />
        {peopleError && <span className="meal-form-error">{peopleError}</span>}
      </label>
      <label className="meal-form-label">
        Number of Dishes
        <input
          className="meal-form-input"
          name="dishes"
          type="number"
          min={1}
          value={form.dishes}
          onChange={handleChange}
          required
        />
        {dishesError && <span className="meal-form-error">{dishesError}</span>}
      </label>
      <label className="meal-form-label">
        Dish Category
        <input
          className="meal-form-input"
          name="dishCategory"
          value={form.dishCategory}
          onChange={handleChange}
          placeholder="e.g. 1 meat, 1 vegetable, 1 starch, 1 dessert"
        />
      </label>
      <label className="meal-form-label">
        Course Type
        <input
          className="meal-form-input"
          name="courseType"
          value={form.courseType}
          onChange={handleChange}
          placeholder="e.g. 1 appetizer, 1 main course, 1 side dish, 1 soup"
        />
      </label>
      <label className="meal-form-label">
        Preferred Cuisine
        <input
          className="meal-form-input"
          name="cuisines"
          value={form.cuisines}
          onChange={handleChange}
          placeholder="e.g. Thai, Italian, Japanese"
        />
      </label>
      <label className="meal-form-label">
        Dietary Option
        <input
          className="meal-form-input"
          name="dietaryRestrictions"
          value={form.dietaryRestrictions}
          onChange={handleChange}
          placeholder="e.g. Vegan, Low-Carb, Dairy-Free"
        />
      </label>
      <button className="meal-form-button" type="submit" disabled={loading}>
        {loading ? 'Planning...' : 'Plan Meal'}
      </button>
    </form>
  );
};

export default MealPlannerForm; 