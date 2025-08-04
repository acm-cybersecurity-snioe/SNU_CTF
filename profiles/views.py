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

        # Define categories (CTF types) - these are the skill areas
        ctf_types = ["STG", "WEB", "NET", "PVE", "ENM"]
        category_labels = ["Steganography", "Web Security", "Networks", "Privilege Escalation", "Enumeration"]
        
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

        return render(request, "profiles/profile_landing.html", {
            "user": request.user,
            "total_points": total_points,
            "categories": categories_json,
            "category_points": category_points_json
        })
    else:
        return render(request, "profiles/guest_profile.html")