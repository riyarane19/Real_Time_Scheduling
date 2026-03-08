cd backend 
python -m pip install --user -r requirements.txt
python -m uvicorn main:app --reload --port 8000

cd frontend
python -m http.server 3000
python -m http.server 3001
