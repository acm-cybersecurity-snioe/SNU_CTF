
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum
from django.http import Http404
from urllib.parse import unquote
from .models import CTFs, UserCTFProgress
import uuid
import mimetypes
from django.db.models.functions import Coalesce
from django.db.models import Value, IntegerField
from django.db.models import Sum, Min, Value, IntegerField
c
# Import supabase client if available
try:
    from .supabase_client import supabase
except ImportError:
    supabase = None


# shows all ctf categories on /ctfs page
def ctf_list(request):
    ctftypes = CTFs.CTF_TYPE
    return render(request, 'ctfs/ctfs.html', {'ctftypes': ctftypes})


# shows all ctfs of a specific type
def ctf_type(request, type):
    type_upper = type.upper()
    ctf_type_dict = dict(CTFs.CTF_TYPE)

    if type_upper not in ctf_type_dict:
        raise Http404("CTF category not found")

    ctfs = CTFs.objects.filter(type=type_upper)
    return render(request, 'ctfs/ctf_type.html', {
        'ctfs': ctfs,
        'type': ctf_type_dict[type_upper]
    })


@login_required
def ctf_detail(request, type, title):
    type_upper = type.upper()
    
    # Decode the URL-encoded title parameter
    decoded_title = unquote(title)
    
    # Debug logging (remove in production)
    print(f"Original title: {title}")
    print(f"Decoded title: {decoded_title}")
    print(f"Looking for CTF with type: {type_upper}, title: {decoded_title}")
    
    try:
        ctf = CTFs.objects.get(type=type_upper, title=decoded_title)
    except CTFs.DoesNotExist:
        # Additional debug info
        print("CTF not found. Available CTFs:")
        for c in CTFs.objects.filter(type=type_upper):
            print(f"  - '{c.title}'")
        raise Http404("No CTFs matches the given query.")

    # Check if already solved
    solved = UserCTFProgress.objects.filter(user=request.user, ctf=ctf).exists()

    if request.method == 'POST':
        user_answer = request.POST.get('answer', '').strip()
        if user_answer.lower() == ctf.solution.lower():
            if solved:
                messages.info(request, "You have already solved this challenge and received points.")
            else:
                UserCTFProgress.objects.create(user=request.user, ctf=ctf, points_awarded=ctf.points)
                messages.success(request, f"Correct answer! You earned {ctf.points} points.")
            return redirect('ctf_detail', type=type, title=title)
        else:
            messages.error(request, "Incorrect answer. Try again!")
            return redirect('ctf_detail', type=type, title=title)

    return render(request, 'ctfs/ctf_details.html', {'ctf': ctf, 'solved': solved})


# Alternative view using slug (recommended for new implementations)
@login_required
def ctf_detail_slug(request, type, slug):
    type_upper = type.upper()
    ctf = get_object_or_404(CTFs, type=type_upper, slug=slug)

    # Check if already solved
    solved = UserCTFProgress.objects.filter(user=request.user, ctf=ctf).exists()

    if request.method == 'POST':
        user_answer = request.POST.get('answer', '').strip()
        if user_answer.lower() == ctf.solution.lower():
            if solved:
                messages.info(request, "You have already solved this challenge and received points.")
            else:
                UserCTFProgress.objects.create(user=request.user, ctf=ctf, points_awarded=ctf.points)
                messages.success(request, f"Correct answer! You earned {ctf.points} points.")
            return redirect('ctf_detail_slug', type=type, slug=slug)
        else:
            messages.error(request, "Incorrect answer. Try again!")
            return redirect('ctf_detail_slug', type=type, slug=slug)

    return render(request, 'ctfs/ctf_details.html', {'ctf': ctf, 'solved': solved})


@login_required
def leaderboard(request):
    leaderboard_data = (
        User.objects
        .annotate(
            total_points=Coalesce(Sum('userctfprogress__points_awarded'), Value(0), output_field=IntegerField()),
            first_solve_time=Min('userctfprogress__solved_at')  # earliest solve timestamp
        )
        .order_by('-total_points', 'first_solve_time')  # primary: highest points, secondary: earliest solve
    )
    return render(request, 'ctfs/leaderboard.html', {'leaderboard': leaderboard_data})


@login_required
def create_ctf(request):
    if not request.user.is_staff:
        messages.error(request, "Only admins can create CTFs.")
        return redirect('ctfs_url')

    if request.method == 'POST':
        title = request.POST.get('title')
        type = request.POST.get('type')
        category = request.POST.get('category')
        description = request.POST.get('description')
        date = request.POST.get('date')
        points = request.POST.get('points')
        solution = request.POST.get('solution')

        image_file = request.FILES.get('image')
        challenge_file = request.FILES.get('challenge_file')

        ctf = CTFs(
            title=title,
            type=type,
            category=category,
            description=description,
            date=date,
            points=points,
            solution=solution
        )

        # Image upload to Supabase (if configured)
        if image_file and supabase:
            try:
                image_ext = image_file.name.split('.')[-1]
                image_name = f"{uuid.uuid4()}.{image_ext}"
                mime_type = mimetypes.guess_type(image_name)[0] or "application/octet-stream"
                image_path = f"ctf-images/{image_name}"
                supabase.storage.from_("ctf-images").upload(image_path, image_file.read(), {"content-type": mime_type})
                image_url = supabase.storage.from_("ctf-images").get_public_url(image_path)
                ctf.image = image_url
            except Exception as e:
                messages.warning(request, f"Image upload failed: {e}")

        # Challenge file upload to Supabase (if configured)
        if challenge_file and supabase:
            try:
                file_ext = challenge_file.name.split('.')[-1]
                file_name = f"{uuid.uuid4()}.{file_ext}"
                mime_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
                file_path = f"ctf-files/{file_name}"
                supabase.storage.from_("ctf-files").upload(file_path, challenge_file.read(), {"content-type": mime_type})
                file_url = supabase.storage.from_("ctf-files").get_public_url(file_path)
                ctf.challange_files = file_url
            except Exception as e:
                messages.warning(request, f"File upload failed: {e}")

        ctf.save()
        messages.success(request, "CTF created successfully.")
        return redirect('ctfs_url')

    return render(request, 'ctfs/create_ctf.html', {
        'ctf_types': CTFs.CTF_TYPE,
        'categories': CTFs.CATEGORIES,
    })