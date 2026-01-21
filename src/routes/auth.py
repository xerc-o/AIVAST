from flask import Blueprint, request, redirect, url_for, flash, render_template, session
from flask_login import login_user, logout_user, login_required
from models import db, User
from extensions import oauth
import os

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login/google")
def google_login():
    """Initiates the Google OAuth2 flow."""
    redirect_uri = url_for('auth.authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route("/authorize")
def authorize():
    """Handles the callback from Google."""
    token = oauth.google.authorize_access_token()
    user_info = token.get('userinfo')
    
    if not user_info:
        flash('Failed to retrieve user information from Google.')
        return redirect(url_for('main.index'))

    email = user_info['email']
    google_id = user_info['sub']
    username = user_info.get('name', email.split('@')[0])
    profile_pic = user_info.get('picture')

    # Find or create user
    user = User.query.filter_by(email=email).first()
    
    if not user:
        # Create a new user if they don't exist
        user = User(
            email=email,
            username=username,
            google_id=google_id,
            profile_pic=profile_pic
        )
        db.session.add(user)
    else:
        # Update existing user's Google info
        user.google_id = google_id
        user.profile_pic = profile_pic
        if not user.username:
            user.username = username
            
    db.session.commit()

    # Log the user in
    login_user(user, remember=True)
    return redirect(url_for('main.chat_page'))

@auth_bp.route("/signup_page", methods=["GET"])
def signup_page():
    # Now just redirects to index since we only use Google Login
    return redirect(url_for('main.index'))

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
