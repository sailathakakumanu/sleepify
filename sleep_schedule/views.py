import json
import firebase_admin
from firebase_admin import auth, credentials, firestore
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from google.generativeai import configure, generate_text

# Initialize Firebase
cred = credentials.Certificate("path/to/your/firebase-adminsdk.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Initialize Gemini AI
configure(api_key="YOUR_GEMINI_API_KEY")

@csrf_exempt
def google_sign_in(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            id_token = data.get("idToken")
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token["uid"]
            email = decoded_token.get("email")

            # Check if user exists in Firestore
            user_ref = db.collection("users").document(uid)
            user_doc = user_ref.get()

            if not user_doc.exists:
                user_ref.set({"email": email, "sleep_schedule": None})

            return JsonResponse({"message": "User authenticated", "uid": uid}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
def get_sleep_schedule(request, uid):
    try:
        user_doc = db.collection("users").document(uid).get()
        if user_doc.exists:
            return JsonResponse(user_doc.to_dict(), status=200)
        return JsonResponse({"error": "User not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def generate_sleep_schedule(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            uid = data.get("uid")
            sleep_preferences = data.get("preferences")

            if not uid or not sleep_preferences:
                return JsonResponse({"error": "Missing parameters"}, status=400)

            # Generate AI-powered sleep schedule
            prompt = f"Generate a personalized sleep schedule based on {sleep_preferences}"
            response = generate_text(prompt=prompt)

            if response.result:
                sleep_schedule = response.result
                db.collection("users").document(uid).update({"sleep_schedule": sleep_schedule})
                return JsonResponse({"message": "Sleep schedule generated", "schedule": sleep_schedule}, status=200)

            return JsonResponse({"error": "Failed to generate schedule"}, status=500)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    
    return JsonResponse({"error": "Invalid request"}, status=400)
def home(request):
    return JsonResponse({"message": "Welcome to the Sleep Scheduler API"})
