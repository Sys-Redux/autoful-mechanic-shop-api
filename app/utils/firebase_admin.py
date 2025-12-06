import firebase_admin
from firebase_admin import credentials, auth
import os
import json

_initialized = False


def initialize_firebase():
    """
    Initialize Firebase Admin SDK.
    Returns True if initialized successfully, False otherwise.
    """
    global _initialized
    if _initialized:
        return True

    cred = None

    service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
    if service_account_json:
        try:
            service_account_info = json.loads(service_account_json)
            cred = credentials.Certificate(service_account_info)
        except json.JSONDecodeError as e:
            print(f'Error parsing FIREBASE_SERVICE_ACCOUNT_JSON: {e}')
            return False

    if not cred:
        # No credentials available - this is expected in test environments
        return False

    try:
        firebase_admin.initialize_app(cred)
        _initialized = True
        return True
    except Exception as e:
        print(f'Error initializing Firebase: {e}')
        return False


def is_firebase_initialized() -> bool:
    """Check if Firebase Admin SDK is initialized."""
    return _initialized


def verify_firebase_token(id_token: str) -> dict | None:
    """
    Verify a Firebase ID token & return decoded claims.

    Args:
        id_token: The Firebase ID token (JWT) from Authorization header

    Returns:
        dict w/ user info ('uid', 'email', 'email_verified', etc.)
        or None if invalid/expired or Firebase not initialized
    """
    # Don't attempt verification if Firebase isn't initialized
    if not _initialized:
        return None

    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except auth.InvalidIdTokenError as e:
        print(f'Invalid Firebase token: {e}')
        return None
    except auth.ExpiredIdTokenError as e:
        print(f'Expired Firebase token: {e}')
        return None
    except auth.RevokedIdTokenError as e:
        print(f'Revoked Firebase token: {e}')
        return None
    except auth.CertificateFetchError as e:
        print(f'Error fetching Firebase certificates: {e}')
        return None
    except Exception as e:
        print(f'Error verifying Firebase token: {e}')
        return None


def set_user_claims(firebase_uid: str, role: str, db_id: int) -> bool:
    """
    Set custom claims for a Firebase user.
    Links the Firebase user to the database and sets their role.

    Must be called after creating a user in database.

    Note:
        User must sign out and back in to see new claims in their token.
    """
    if not _initialized:
        print('Firebase not initialized - cannot set claims')
        return False

    try:
        auth.set_custom_user_claims(firebase_uid, {
            'role': role,
            'db_id': db_id
        })
        return True
    except auth.UserNotFoundError:
        print(f'Firebase user not found: {firebase_uid}')
        return False
    except Exception as e:
        print(f'Error setting custom claims for {firebase_uid}: {e}')
        return False


def get_user_claims(firebase_uid: str) -> dict | None:
    """Get custom claims for a Firebase user."""
    if not _initialized:
        return None

    try:
        user = auth.get_user(firebase_uid)
        return user.custom_claims or {}
    except auth.UserNotFoundError:
        print(f'Firebase user not found: {firebase_uid}')
        return None
    except Exception as e:
        print(f'Error fetching user claims for {firebase_uid}: {e}')
        return None