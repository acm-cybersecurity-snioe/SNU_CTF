from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from ctfs.models import UserCTFProgress, CTFs
from django.db.models.functions import Coalesce
from django.db.models import Sum
from django.db.models import Value, IntegerField
import json

def profile_landing(request):
    if request.user.is_authenticated:
        # calculate total points from solved CTFs
        total_points = (
            UserCTFProgress.objects
            .filter(user=request.user)
            .aggregate(points=Coalesce(Sum('points_awarded'), Value(0), output_field=IntegerField()))
        )['points']

        # Define categories (CTF types)
        ctf_types = ["STG", "WEB", "NET", "PVE", "ENM", "REV"]
        category_labels = ["Steganography", "Web Security", "Networks", "Privilege Escalation", "Enumeration", "Reverse Engineering"]
        
        # Calculate points per CTF type
        category_points = []
        for ctf_type in ctf_types:
            points = UserCTFProgress.objects.filter(
                user=request.user,
                ctf__type=ctf_type  # Filter by CTF type
            ).aggregate(
                points=Coalesce(Sum('points_awarded'), Value(0), output_field=IntegerField())
            )['points']
            category_points.append(points)

        # Convert to JSON for JavaScript
        categories_json = json.dumps(category_labels)
        category_points_json = json.dumps(category_points)

        #fro subscription 
        subscription, _ = Subscription.get_or_create_for_user(request.user)


        return render(request, "profiles/profile_landing.html", {
            "user": request.user,
            "total_points": total_points,
            "categories": categories_json,
            "category_points": category_points_json,
            "subscription": subscription,
        })    
    else:
        return render(request, "profiles/guest_profile.html")

from .models import Subscription 
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages

@login_required
@require_POST
@csrf_protect
def subscription(request):

    try :
        subscription ,created = Subscription.objects.get_or_create(
            user=request.user,
            defaults={'subscription_choice': False}
        )

        subscription.subscription_choice = not subscription.subscription_choice
        subscription.save()

        if subscription.subscription_choice:
            messages.success(request, "✅ You've subscribed to email notifications!")
        else:
            messages.info(request, "❌ You've unsubscribed from email notifications.")

    except Exception as e:
        messages.error(request, "⚠️ Something went wrong. Please try again.")
        # Log the error for debugging
        print(f"Subscription toggle error for {request.user.username}: {e}")
    
    # Redirect back to profile
    return redirect('profile_landing')