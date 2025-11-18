import django
import requests
from django.contrib.auth import get_user_model

django.setup()

BASE_URL = "http://localhost:8000"  # ou "http://127.0.0.1:8000"
USER_CREATE_URL = f"{BASE_URL}/api/user/"
TOKEN_URL = f"{BASE_URL}/api/token/"

SU_USERNAME = "admin"
SU_EMAIL = "admin@example.com"
SU_PASSWORD = "SuperPassword123"
U1_USERNAME = "user1"
U1_EMAIL = "user1@example.com"
U1_PASSWORD = "SuperPassword123"
U2_USERNAME = "user2"
U2_EMAIL = "user2@example.com"
U2_PASSWORD = "SuperPassword123"

User = get_user_model()
# ----------------------   CREATE SUPERUSER ----------------------------
print("\nCREATE SUPERUSER")
if not User.objects.filter(username=SU_USERNAME).exists():
    User.objects.create_superuser(
        username=SU_USERNAME,
        email=SU_EMAIL,
        password=SU_PASSWORD
    )
    print("Superuser created.")
else:
    print("Superuser already exists.")

# -------------------------- CREATE USER1 ---------------------------------
print("\nCREATE USER U1")
if not User.objects.filter(username=SU_USERNAME).exists():
    u1 = User.objects.create_user(
        username=U1_USERNAME,
        email=U1_EMAIL,
        password=U1_PASSWORD
    )
    print("\nUtilisateur créé :", u1)
else:
    print("\nUtilisateur existe déjà.")

# --------------------------- CREATE USER 2 -----------------------------------

print("\nCREATE USER U2")
payload = {"username": U2_USERNAME, "email": U2_EMAIL, "first_name": U2_USERNAME, "last_name": U2_USERNAME,
           "password": U2_PASSWORD, }
response = requests.post(USER_CREATE_URL, json=payload)
response.raise_for_status()  # lève une exception si statut >= 400
user_data = response.json()
print("\nUtilisateur créé :", user_data)
u2_id = user_data["id"]

# ------------------------ SU GET TOKEN ---------------------------------

print("\nRécupération du token SU")
payload = {
    "username": SU_USERNAME,
    "password": SU_PASSWORD,
}
response = requests.post(TOKEN_URL, json=payload)
response.raise_for_status()
data = response.json()
su_token = data["access"]
print("\nSU Access token :", su_token)

# ------------------------ U2 GET TOKEN ---------------------------------

print("\nRécupération du token U2")
payload = {
    "username": U2_USERNAME,
    "password": U2_PASSWORD,
}
response = requests.post(TOKEN_URL, json=payload)
response.raise_for_status()
data = response.json()
u2_token = data["access"]
print("\nSU Access token :", u2_token)

# ------------------------ SU LIST USERS ---------------------------------

print("\nLIST USERS SU")
headers = {
    "Authorization": f"Bearer {su_token}",
}
try :
    response = requests.get(USER_CREATE_URL, headers=headers, timeout=5)
    response.raise_for_status()
    data = response.json()
    print("\nRéponse de la requête :", data)
    for item in data:
        print(item)
except Exception as e:
        print("Erreur ", e.response.status_code, " : ", e.response.text)

# ------------------------ U2 LIST USERS ---------------------------------

print("\nLIST USERS U2")
headers = {
    # Pour SimpleJWT :
    "Authorization": f"Bearer {u2_token}",
    "Content-Type": "application/json",
}
try :
    response = requests.get(USER_CREATE_URL, headers=headers, timeout=5)
    response.raise_for_status()

    data = response.json()
    print("\nRéponse de la requête :")
    for item in data:
        print(item)
except Exception as e:
        print("Erreur ", e.response.status_code, " : ", e.response.text)

