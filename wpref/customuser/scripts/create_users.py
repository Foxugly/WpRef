from django.contrib.auth import get_user_model

User = get_user_model()
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "SuperPassword123"
ADMIN_EMAIL = "admin@example.com"
U1_USERNAME = "user1"
U1_EMAIL = "user1@example.com"
U1_PASSWORD = "SuperPassword123"


def run():
    # ----------------------   CREATE SUPERUSER ----------------------------
    print("\nCREATE SUPERUSER")
    if not User.objects.filter(username=ADMIN_USERNAME).exists():
        User.objects.create_superuser(
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            password=ADMIN_PASSWORD
        )
        print("Superuser created.")
    else:
        print("Superuser already exists.")
    # -------------------------- CREATE USER1 ---------------------------------
    print("\nCREATE USER U1")
    if not User.objects.filter(username=U1_USERNAME).exists():
        u1 = User.objects.create_user(
            username=U1_USERNAME,
            first_name=U1_USERNAME,
            last_name=U1_USERNAME,
            email=U1_EMAIL,
            password=U1_PASSWORD
        )
        print("\nUtilisateur créé :", u1)
    else:
        print("\nUtilisateur existe déjà.")
