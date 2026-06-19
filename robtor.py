"""
Robtor MCP Server - Bilingual (Hindi + English)
Bridges Xiaozhi AI Agent <-> Supabase Database
Deploy on Railway/Render (free)
"""
from dotenv import load_dotenv
load_dotenv()
from mcp.server.fastmcp import FastMCP
from supabase import create_client, Client
import requests
import os
from datetime import datetime

SUPABASE_URL = os.getenv("SUPABASE_URL", "your_supabase_url")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your_supabase_anon_key")
CALLMEBOT_API_KEY = os.getenv("CALLMEBOT_API_KEY", "your_callmebot_key")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
mcp = FastMCP("Robtor Health Assistant")

def get_uid_by_name(name: str):
    result = supabase.table("profiles").select("id").ilike("full_name", f"%{name}%").limit(1).execute()
    if result.data:
        return result.data[0]["id"]
    return None

@mcp.tool()
def get_user_profile(name: str) -> str:
    """
    EN: Fetch user profile. Use when user says their name or asks about profile.
    HI: Jab user apna naam bataye ya profile pooche.
    Keywords EN: my profile, who am I, my details, my info
    Keywords HI: mera profile, meri details, main kaun hoon, meri jaankari
    """
    uid = get_uid_by_name(name)
    if not uid:
        return f"'{name}' ka profile nahi mila. Robtor app mein profile banao pehle."
    profile = supabase.table("user_profile").select("*").eq("id", uid).single().execute()
    if not profile.data:
        return "Profile data nahi mila."
    d = profile.data
        return f"""
    Naam: {d.get('name','N/A')}
    Age: {d.get('age','N/A')}
    Gender: {d.get('gender','N/A')}
    Weight: {d.get('weight','N/A')} kg
    Height: {d.get('height','N/A')} cm
    BMI: {d.get('bmi','N/A')}
    Goal: {d.get('weight_goal','N/A')}
    Conditions: {d.get('conditions',[])}
    """

@mcp.tool()
def get_health_summary(user_name: str) -> str:
    """
    EN: Full health summary. Use for any general health question.
    HI: Jab user overall health ke baare mein pooche.
    Keywords EN: health summary, how is my health, overall health, body condition
    Keywords HI: health kaisi hai, sehat kaisi hai, meri health batao, body kaisi hai, sab theek hai kya, mujhe kya ho raha hai
    """
    uid = get_uid_by_name(user_name)
    if not uid:
        return "Profile nahi mila. Pehle apna naam batao."
    risks = supabase.table("health_risks").select("risk_name,risk_level").eq("user_id", uid).order("risk_level", desc=True).limit(3).execute()
    wearable = supabase.table("wearable_data").select("steps,sleep_hours,heart_rate,date").eq("user_id", uid).order("date", desc=True).limit(1).execute()
    symptoms = supabase.table("symptom_logs").select("symptom,severity").eq("user_id", uid).order("logged_at", desc=True).limit(3).execute()
    summary = "Sehat ka Haal:\n"
    if wearable.data:
        w = wearable.data[0]
        summary += f"Steps: {w.get('steps','N/A')}, Neend: {w.get('sleep_hours','N/A')}hrs, HR: {w.get('heart_rate','N/A')}bpm\n"
    if risks.data:
        summary += "Risks: " + ", ".join([f"{r['risk_name']}({r['risk_level']})" for r in risks.data]) + "\n"
    if symptoms.data:
        summary += "Recent symptoms: " + ", ".join([s['symptom'] for s in symptoms.data])
    return summary

@mcp.tool()
def get_medications(user_name: str) -> str:
    """
    EN: Get medicines and schedule. Use for any medicine question.
    HI: Dawai ya tablet ke baare mein pooche tab use karo.
    Keywords EN: medicine, tablet, pill, medication, when to take medicine, my medicines, reminder
    Keywords HI: dawai, dawa, tablet, kya khana hai, meri dawai, dawai kab leni hai, medicine reminder
    """
    uid = get_uid_by_name(user_name)
    if not uid:
        return "Profile nahi mila."
    meds = supabase.table("medication_reminders").select("*").eq("user_id", uid).eq("is_active", True).execute()
    if not meds.data:
        return "Koi active dawai nahi mili."
    result = "Teri Dawaiyan:\n"
    for m in meds.data:
        result += f"- {m.get('medication_name')} | Dose: {m.get('dosage')} | Time: {m.get('reminder_time')} | {m.get('frequency')}\n"
    return result

@mcp.tool()
def get_diet_plan(user_name: str) -> str:
    """
    EN: Get diet and meal plan. Use for any food or eating question.
    HI: Khane ya diet ke baare mein pooche tab use karo.
    Keywords EN: diet, food, meal, what to eat, breakfast, lunch, dinner, nutrition, calories, healthy eating
    Keywords HI: kya khaaun, khana, diet plan, kya khaana chahiye, aaj kya khaaun, healthy khana, diet batao, breakfast kya khaaun
    """
    uid = get_uid_by_name(user_name)
    if not uid:
        return "Profile nahi mila."
    diet = supabase.table("diet_plan").select("*").eq("user_id", uid).order("created_at", desc=True).limit(1).execute()
    if not diet.data:
        return "Diet plan nahi mila. Robtor app mein generate karo."
    d = diet.data[0]
    return f"Diet Plan:\nSubah: {d.get('breakfast')}\nDopahar: {d.get('lunch')}\nRaat: {d.get('dinner')}\nSnacks: {d.get('snacks')}\nCalories: {d.get('daily_calories')} kcal\nNotes: {d.get('notes')}"

@mcp.tool()
def get_fitness_plan(user_name: str) -> str:
    """
    EN: Get workout and exercise plan. Use for any fitness question.
    HI: Exercise ya workout ke baare mein pooche tab use karo.
    Keywords EN: exercise, workout, gym, fitness, running, yoga, weight loss, muscle, cardio, physical activity
    Keywords HI: exercise, vyayam, workout, gym, fitness, body banana, weight loss, daudna, yoga, aaj kya karna hai gym mein
    """
    uid = get_uid_by_name(user_name)
    if not uid:
        return "Profile nahi mila."
    fitness = supabase.table("fitness_plan").select("*").eq("user_id", uid).order("created_at", desc=True).limit(1).execute()
    if not fitness.data:
        return "Fitness plan nahi mila."
    f = fitness.data[0]
    return f"Fitness Plan:\nGoal: {f.get('goal')}\nWeekly Sessions: {f.get('weekly_sessions')}\nAaj ka workout: {f.get('today_workout')}\nDuration: {f.get('duration_minutes')} min\nNotes: {f.get('notes')}"

@mcp.tool()
def get_lab_results(user_name: str) -> str:
    """
    EN: Get lab test results and biomarkers. Use for any report question.
    HI: Lab report ya test results ke baare mein pooche tab use karo.
    Keywords EN: report, lab results, blood test, CBC, hemoglobin, sugar, cholesterol, test results, biomarker
    Keywords HI: report, lab report, khoon ki jaanch, blood test, meri report, test kya aaya, haemoglobin, sugar level, report batao
    """
    uid = get_uid_by_name(user_name)
    if not uid:
        return "Profile nahi mila."
    labs = supabase.table("lab_results").select("*").eq("user_id", uid).order("test_date", desc=True).limit(1).execute()
    if not labs.data:
        return "Koi lab result nahi mila. Robtor app mein report upload karo."
    l = labs.data[0]
    return f"Lab Results ({l.get('test_date')}):\nTest: {l.get('test_name')}\nHaemoglobin: {l.get('hemoglobin')} g/dL\nBlood Sugar: {l.get('blood_sugar')} mg/dL\nCholesterol: {l.get('cholesterol')} mg/dL\nStatus: {l.get('overall_status')}\nNotes: {l.get('notes')}"

@mcp.tool()
def get_health_risks(user_name: str) -> str:
    """
    EN: Get future health risk predictions. Use for any risk or prevention question.
    HI: Future health risks ke baare mein pooche tab use karo.
    Keywords EN: risk, future health, what can happen, health warning, prevention, health prediction
    Keywords HI: khatara, future health, mujhe kya ho sakta hai, bimari ka khatara, kya savdhani rakhu, health risk batao, aagebhi kya hoga
    """
    uid = get_uid_by_name(user_name)
    if not uid:
        return "Profile nahi mila."
    risks = supabase.table("health_risks").select("*").eq("user_id", uid).order("overall_risk_score", desc=True).execute()
    if not risks.data:
        return "Koi health risk data nahi mila."
    result = "Health Risks:\n"
    for r in risks.data:
        result += f"- {r.get('category')} | Current: {r.get('current_risk')} | Future: {r.get('future_risk_6months')} | Reason: {r.get('reason')} | Prevention: {r.get('prevention_tip')}\n"
    return result

@mcp.tool()
def get_wearable_summary(user_name: str) -> str:
    """
    EN: Get wearable data - steps, sleep, heart rate. Use for activity questions.
    HI: Steps, neend, heart rate ke baare mein pooche tab use karo.
    Keywords EN: steps, sleep, heart rate, activity, calories, wearable, fitness tracker, how much walked, active minutes
    Keywords HI: steps, kitna chala, neend, heart rate, dil ki dhadkan, calories, aaj kitna chala, watch data, activity data
    """
    uid = get_uid_by_name(user_name)
    if not uid:
        return "Profile nahi mila."
   data = supabase.table("wearable_data").select("*").eq("user_id", uid).order("synced_at", desc=True).limit(1).execute()
    if not data.data:
        return "Koi wearable data nahi mila."
    w = data.data[0]
        return f"""
    Wearable Data:
    Steps: {w.get('avg_daily_steps')}
    Sleep: {w.get('avg_sleep_hours')} hrs
    Resting Heart Rate: {w.get('resting_heart_rate')} bpm
    Calories Burned: {w.get('calories_burned')}
    Source Device: {w.get('source_device')}
    Last Sync: {w.get('synced_at')}
    """

@mcp.tool()
def log_symptom(user_name: str, symptom: str, severity: str = "mild") -> str:
    """
    EN: Log any health complaint - casual or direct. AUTO-LOG if user mentions ANY body issue.
    HI: User jo bhi health complaint bataye casually ya seedha - automatically note karo.
    Keywords EN: pain, headache, fever, tired, weak, nausea, cough, breathless, chest pain, body pain, not feeling well, dizzy
    Keywords HI: dard, sir dard, bukhar, thakan, kamzori, ulti, khansi, saans, chest pain, tabiyat theek nahi, chakkar, mujhe ho raha hai
    AUTO-TRIGGER: Even if user says casually 'kal se dard hai' or 'thoda tired hoon' - log it.
    severity options: mild / moderate / severe
    """
    uid = get_uid_by_name(user_name)
    if not uid:
        return "Profile nahi mila."
    supabase.table("symptom_logs").insert({
        "user_id": uid,
        "symptom": symptom,
        "severity": severity,
        "logged_at": datetime.utcnow().isoformat(),
        "source": "voice_assistant"
    }).execute()
    return f"Note kar liya! '{symptom}' teri health history mein save ho gaya."

@mcp.tool()
def save_conversation_health_log(user_name: str, user_message: str, agent_response: str, symptoms_detected: str = "", mood: str = "neutral") -> str:
    """
    EN: ALWAYS call this after every conversation turn to save health context.
    HI: Har conversation ke baad automatically call karo - doctor ke liye record rakhne ke liye.
    IMPORTANT: Call this after EVERY message automatically without user asking.
    mood: positive / negative / neutral / anxious / happy
    """
    uid = get_uid_by_name(user_name)
    if not uid:
        return "Profile nahi mila."
    supabase.table("conversation_health_logs").insert({
        "user_id": uid,
        "date": datetime.utcnow().date().isoformat(),
        "user_message": user_message,
        "agent_response": agent_response,
        "symptoms_detected": symptoms_detected,
        "mood": mood,
        "created_at": datetime.utcnow().isoformat(),
        "source": "robtor_pod"
    }).execute()
    return "Conversation saved."

@mcp.tool()
def trigger_emergency(user_name: str, situation: str = "Emergency") -> str:
    """
    EN: EMERGENCY - Trigger INSTANTLY. No confirmation needed. Act immediately.
    HI: EMERGENCY - Seedha trigger karo. Koi confirmation mat maango. Turant karo.

    TRIGGER INSTANTLY for these words:
    EN: help, emergency, call now, chest pain, not breathing, unconscious, accident, dying, falling, cant breathe
    HI: bachao, madad karo, emergency hai, call karo, ambulance, doctor bulao, hospital, bahut dard, saans nahi, behosh, gir gaya, mar raha hoon

    DO NOT ask 'are you sure?' - just trigger immediately.
    Sends WhatsApp to ALL emergency contacts right away.
    """
    uid = get_uid_by_name(user_name)
    contacts = []
    if uid:
        result = supabase.table("emergency_contacts").select("*").eq("user_id", uid).execute()
        contacts = result.data or []

    profile_info = "Unknown User"
    if uid:
       profile = supabase.table("user_profile").select("*").eq("id", uid).single().execute()
        if profile.data:
            p = profile.data
            profile_info = f"Naam: {p.get('name')} | Umar: {p.get('age')} | Gender: {p.get('gender')} | Conditions: {p.get('conditions',[])}"

    message = f"""ROBTOR EMERGENCY ALERT

Mareez / Patient:
{profile_info}

Situation: {situation}
Samay / Time: {datetime.now().strftime('%d/%m/%Y %I:%M %p')}

TURANT KARO / DO NOW:
1. 112 pe call karo / Call 112 NOW
2. Patient ko litao / Lay patient down
3. Khana paani mat do / No food or water
4. Saans check karo / Check breathing
5. Paas raho jab tak madad aaye / Stay until help arrives

Yeh alert Robtor Health Pod ne bheja hai."""

    sent_to = []
    for contact in contacts:
        phone = contact.get("phone_number", "")
        name = contact.get("contact_name", "Contact")
        if phone:
            try:
                requests.get(
                    "https://api.callmebot.com/whatsapp.php",
                    params={"phone": phone, "text": message, "apikey": CALLMEBOT_API_KEY},
                    timeout=10
                )
                sent_to.append(name)
            except Exception as e:
                print(f"Error sending to {name}: {e}")

    if uid:
        supabase.table("symptom_logs").insert({
            "user_id": uid,
            "symptom": f"EMERGENCY: {situation}",
            "severity": "severe",
            "logged_at": datetime.utcnow().isoformat(),
            "source": "emergency_trigger"
        }).execute()

    if sent_to:
        return f"EMERGENCY ALERT BHI GAYA {', '.join(sent_to)} ko! Madad aa rahi hai. Shaant raho. 112 call ho raha hai."
    else:
        return "EMERGENCY! Koi contact nahi mila. ABHI 112 pe call karo!"

if __name__ == "__main__":
    mcp.run(transport="stdio")
