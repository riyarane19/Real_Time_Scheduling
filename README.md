#Backend (FastAPI + Python)
#Go to backend folder
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:

venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI backend
uvicorn main:app --reload

# Frontend (React + Vite or CRA)
# Go to frontend folder
cd frontend

# Install packages
npm install

# Run development server
npm start    
