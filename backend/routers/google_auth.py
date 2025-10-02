from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import requests
import models, schemas, database, oauth2
from config import settings
from datetime import datetime
import urllib.parse


router = APIRouter(
    tags=["Google OAuth"],
    prefix="/auth/google"
)


@router.get("/login")
async def google_login():
    """Initiate Google OAuth login"""
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.google_client_id}&"
        f"redirect_uri={urllib.parse.quote(settings.google_redirect_uri + '/auth/google/callback')}&"
        f"scope=openid%20email%20profile&"
        f"response_type=code&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    return {"auth_url": auth_url}


@router.get("/callback")
async def google_callback(code: str, db: Session = Depends(database.get_db)):
    """Handle Google OAuth callback and create/login user"""
    try:
        # Exchange authorization code for access token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri + '/auth/google/callback',
            "grant_type": "authorization_code",
        }
        
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        token_json = token_response.json()
        
        if "access_token" not in token_json:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to get access token")
        
        access_token = token_json["access_token"]
        
        # Get user info from Google
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        user_response = requests.get(
            user_info_url, 
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_response.raise_for_status()
        user_info = user_response.json()
        
        # Check if user exists in database
        user = db.query(models.User).filter(models.User.email == user_info["email"]).first()
        
        if not user:
            # Create new user
            new_user_data = {
                "name": user_info.get("name", user_info.get("email", "Unknown")),
                "email": user_info["email"],
                "password": "google_oauth",  # Placeholder password for Google users
                "created_at": datetime.utcnow()
            }
            user = models.User(**new_user_data)
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Generate JWT token for the user
        access_token = oauth2.create_access_token(data={"user_id": user.id})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "created_at": user.created_at
            },
            "login_method": "google"
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Google OAuth error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Authentication failed: {str(e)}")


@router.get("/user")
async def get_google_user_info(current_user: models.User = Depends(oauth2.get_current_user)):
    """Get current authenticated user information"""
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "created_at": current_user.created_at,
        "authentication_method": "google" if current_user.password == "google_oauth" else "regular"
    }